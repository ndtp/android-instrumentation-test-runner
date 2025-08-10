#!/bin/bash

RESTORE='\033[0m'
RED='\033[00;31m'
YELLOW='\033[00;33m'
BLUE='\033[00;36m'
GREEN='\033[00;32m'

error()
{
    echo -e "${RED}[ERROR] ${1}${RESTORE}" >&2
}

warn()
{
    echo -e "${YELLOW}[WARNING] ${1} ${RESTORE}" >&2
}

info()
{
    echo -e "${BLUE}[INFO]${RESTORE} ${1}" >&2
}

success()
{
    echo -e "${GREEN}[SUCCESS]${RESTORE} ${1}" >&2
}

verbose()
{
    if [ "$verbose" == true ] || [ "$VERBOSE" == true ]; then
        warn "$1"
    fi
}

assert_emulator()
{
    if [ "`adb shell getprop sys.boot_completed | tr -d '\r' `" != "1" ] ; then
        error "Emulator not found"
        exit 1
    fi
}

install_apk()
{
    local apk=$1
    local package=$2
    local type=$3

    verbose $(adb logcat -m 1 -d)

    info "Install $apk"
    install_output="$( { adb install -r "$apk"; } 2>&1 )"
    verbose "install_output:"
    verbose "$install_output"

    info "Verify installation"
    verbose "package:"
    verbose "$package"

    instrumentation=$(adb shell pm list "$3")
    verbose "instrumentation:"
    verbose "$instrumentation"

    if [[ $instrumentation =~ "$package" ]]; then
       success "Package $package verified"
    else
        echo "$instrumentation"
        error "Failed to install $apk"
        exit 1
    fi

    if [[ "$install_output" =~ "failed" ]]; then
        echo "$install_output"
        error "Failed to install $apk"
        exit 1
    else
        ok_results=$(echo "$install_output" | grep --color=no "Success")
        success "$ok_results"
    fi
}

invoke_adb_command()
{
    if [ -n "$shard_count" ] && [ "$shard_count" -gt "0" ]; then
        shard="-e numShards $shard_count -e shardIndex $shard_index"
    fi

    if [ ! -z "$annotation" ]; then
        annotation_arg="-e annotation $annotation"
    fi

      if [ ! -z "$not_annotation" ]; then
          not_annotation_arg="-e notAnnotation $not_annotation"
      fi

    local adb_command="adb shell am instrument -r -w $shard $annotation_arg $not_annotation_arg $test_package/$test_runner"

    info "Running '$adb_command'..."
    adb logcat -c
    adb_command_output="$( { $adb_command; } 2>&1 )"
    logcat_output=$(adb logcat -d)

    verbose "adb_command_output:"
    verbose "$adb_command_output"

    verbose ""
    verbose "logcat_output:"
    verbose "$logcat_output"
}

pretty_results()
{
    info "pretty_results()"

    verbose "Create directory ./reports/"
    mkdir -p "./reports/"

    verbose "adb_command_output:"
    verbose "$adb_command_output"

    echo "$adb_command_output" | java -jar "$SCRIPT_DIR/pretty.jar"
}

exit_error()
{
    echo "$adb_command_output"
    echo "$logcat_output"
    error "Tests failed $1"
    exit 1
}

verify_test_status()
{
    info "Verify test status"
    if [[ $adb_command_output =~ "crashed" ]]; then
        exit_error "crashed"
    fi

    if [[ $adb_command_output =~ "Error in" ]]; then
        exit_error "exeception"
    fi

    if [[ $adb_command_output =~ "failures:" ]]; then
        exit_error "failures"
    fi

    if [[ $adb_command_output =~ "failure:" ]]; then
        exit_error "failure"
    fi

    if [[ $adb_command_output =~ "androidx.test.espresso.PerformException" ]]; then
        exit_error "androidx.test.espresso.PerformException"
    fi

    if [[ $adb_command_output =~ "java.util.concurrent.TimeoutException" ]]; then
        exit_error "java.util.concurrent.TimeoutException"
    fi

    if [[ $logcat_output =~ "FAILURES!!!" ]]; then
        exit_error "FAILURES!!!"
    fi

    if [[ $logcat_output =~ "INSTRUMENTATION_CODE: 0" ]]; then
        exit_error "INSTRUMENTATION_CODE: 0"
    fi

    if [[ $logcat_output =~ "Process crashed while executing" ]]; then
        exit_error "Process crashed while executing"
    fi

    ok_results=$(echo "$adb_command_output" | grep --color=no "OK")
    success "$ok_results"

    exit 0
}

load_input_arguments()
{
    export app_apk="${1:-${APP_APK}}"
    export app_package="${2:-${APP_PACKAGE}}"
    export test_apk="${3:-${TEST_APK}}"
    export test_package="${4:-${TEST_PACKAGE}}"
    export test_runner="${5:-${TEST_RUNNER}}"
    export shard_count="${6:-${SHARD_COUNT}}"
    export shard_index="${7:-${SHARD_INDEX}}"
    export annotation="${8:-${ANNOTATION}}"
    export not_annotation="${9:-${NOT_ANNOTATION}}"
    export verbose="${10:-${VERBOSE}}"
}

verify_input_arguments()
{
    info "verify_input_arguments()"
    verbose "app_apk=$app_apk"
    verbose "app_package=$app_package"
    verbose "test_apk=$test_apk"
    verbose "test_package=$test_package"
    verbose "test_runner=$test_runner"
    verbose "shard_count=$shard_count"
    verbose "shard_index=$shard_index"
    verbose "annotation=$annotation"
    verbose "not_annotation=$not_annotation"
    verbose "verbose=$verbose"
}

main()
{
    load_input_arguments "$@"

    if [ "$verbose" == true ] || [ "$VERBOSE" == true ]; then
        info "Verbose mode enabled"
    fi

    verify_input_arguments

    SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    verbose "SCRIPT_DIR: $SCRIPT_DIR"

    assert_emulator
    install_apk $app_apk $app_package package
    install_apk $test_apk $test_package instrumentation

    invoke_adb_command
    pretty_results
    verify_test_status
}

main "$@"

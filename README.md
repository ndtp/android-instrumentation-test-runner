# android-instrumentation-test-runner

GitHub Action to run Android Instrumentation tests.


## Prerequisites

A running Android Emulator is required prior to invoking this action.

- https://github.com/ndtp/enable-kvm-action is recommended for enabling KVM support on GitHub.
- https://github.com/ndtp/android-emulator-runner is recommend for launching and configuring an emulator on GitHub Actions.


## Usage

```
- name: Enable KVM group perms
  uses: ndtp/enable-kvm-action@v1

- name: Boot emulator
  uses: ndtp/android-emulator-runner@main
  with:
    api-level: 29
    target: google_apis
    arch: x86_64
    profile: pixel_3a
    script: adb devices

- name: Run instrumentation tests
  uses: ndtp/android-instrumentation-test-runner@main

```

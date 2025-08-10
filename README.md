# android-instrumentation-test-runner

GitHub Action to run Android Instrumentation tests.

- Installs the provided APK on the emulator.
- Installs the provided test APK on the emulator.
- Runs the instrumentation tests using `adb shell am instrument`.
- Supports running tests on a specific annotation, package or class.
- Parses the test results and uploads them as artifacts.
- Produces JUnit XML test reports compatible with GitHub Actions.

## Prerequisites

A running Android Emulator is required prior to invoking this action.

- https://github.com/ndtp/android-avd-manager-action is recommended for creating an Android Emulator on GitHub Actions.
- https://github.com/ndtp/enable-kvm-action is recommended for enabling KVM support on GitHub.
- https://github.com/ndtp/android-emulator-runner is recommend for launching and configuring an emulator on GitHub Actions.


## Usage

```
- name: Create AVD
  id: create
  uses: ndtp/android-avd-manager-action@main
  with:
    api-level: 29
    target: google_apis
    arch: x86_64
    profile: pixel_3a

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

## License

MIT License

Copyright (c) 2025 ndtp

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.example.credit_pulse"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = "27.0.12077973"

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.example.credit_pulse"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        applicationId = "com.example.credit_pulse"
        minSdkVersion(23)
    }
        signingConfigs {
        create("release") {
            keyAlias = "creditsync"
            keyPassword = "pamerick74*"
            storeFile = file("my-release-key.jks")
            storePassword = "pamerick74*"
        }
    }

    buildTypes {
        release {
        signingConfig = signingConfigs.getByName("release")
    }
    }
}


flutter {
    source = "../.."
}

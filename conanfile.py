import glob
import os

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration

class SpirvToolsConan(ConanFile):
    name = "spirv-tools"
    description = "SPIRV-Cross is a practical tool and library for performing " \
                  "reflection on SPIR-V and disassembling SPIR-V back to high level languages."
    license = "Apache-2.0"
    topics = ("conan", "spirv-tools", "spirv", "spirv-v", "vulkan", "opengl", "opencl", "hlsl", "khronos")
    homepage = "https://github.com/KhronosGroup/SPIRV-Tools"
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = "CMakeLists.txt"
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "c_api_only": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "c_api_only": False
    }

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.compiler.cppstd:
            tools.check_min_cppstd(self, 11)

    def requirements(self):
        self.requires.add("spirv-headers/1.5.1")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("SPIRV-Tools-" + self.version, self._source_subfolder)

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def _patch_sources(self):
        # don't force PIC
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "set(CMAKE_POSITION_INDEPENDENT_CODE ON)", "")

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        if self.options.shared:
            if self.options.c_api_only:
                self._cmake.definitions["BUILD_SHARED_LIBS"] = False
            elif self.settings.compiler == "Visual Studio":
                self._cmake.definitions["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = True
        self._cmake.definitions["SKIP_SPIRV_TOOLS_INSTALL"] = False
        self._cmake.definitions["SPIRV_WERROR"] = False
        self._cmake.definitions["SPIRV_LOG_DEBUG"] = False
        self._cmake.definitions["SPIRV_SKIP_EXECUTABLES"] = False
        self._cmake.definitions["SPIRV_SKIP_TESTS"] = True
        self._cmake.definitions["SPIRV_CHECK_CONTEXT"] = False
        self._cmake.definitions["SPIRV-Headers_SOURCE_DIR"] = self.deps_cpp_info["spirv-headers"].rootpath
        self._cmake.definitions["SPIRV_BUILD_FUZZER"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        self._cleanup_package_folder()

    def _cleanup_package_folder(self):
        # Remove unwanted header files
        if self.options.c_api_only:
            for header_file in glob.glob(os.path.join(self.package_folder, "include", "spirv-tools", "*.hpp")):
                os.remove(header_file)
        # Remove unwanted runtime files
        if self.settings.os == "Windows" and not (self.options.c_api_only and self.options.shared):
            os.remove(os.path.join(self.package_folder, "bin", "SPIRV-Tools-shared.dll"))
        # Remove unwanted lib files
        if self.options.c_api_only:
            if self.options.shared:
                for lib_file in glob.glob(os.path.join(self.package_folder, "lib", "*")):
                    if not os.path.splitext(lib_file)[0].endswith(("SPIRV-Tools-shared", "SPIRV-Tools-shared.dll")):
                        os.remove(lib_file)
            else:
                for lib_file in glob.glob(os.path.join(self.package_folder, "lib", "*")):
                    if not os.path.splitext(lib_file)[0].endswith("SPIRV-Tools"):
                        os.remove(lib_file)
        else:
            for lib_file in glob.glob(os.path.join(self.package_folder, "lib", "*")):
                if os.path.splitext(lib_file)[0].endswith(("SPIRV-Tools-shared", "SPIRV-Tools-shared.dll")):
                    os.remove(lib_file)

    def package_info(self):
        # TODO: set targets names when components available in conan
        if self.options.c_api_only:
            if self.options.shared:
                self.cpp_info.libs = ["SPIRV-Tools-shared"]
                self.cpp_info.defines.append("SPIRV_TOOLS_SHAREDLIB")
            else:
                self.cpp_info.libs = ["SPIRV-Tools"]
        else:
            self.cpp_info.libs = ["SPIRV-Tools-reduce", "SPIRV-Tools-link", "SPIRV-Tools-opt", "SPIRV-Tools"]
        if self.settings.os == "Linux":
            self.cpp_info.defines.append("rt") # for SPIRV-Tools
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))

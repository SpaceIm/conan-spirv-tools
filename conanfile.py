import glob
import os

from conans import ConanFile, CMake, tools

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
    short_paths = True
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

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
        self.requires.add("spirv-headers/1.5.3")

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
        if self.options.shared and self.settings.compiler == "Visual Studio":
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
        tools.rmdir(os.path.join(self.package_folder, "SPIRV-Tools"))
        tools.rmdir(os.path.join(self.package_folder, "SPIRV-Tools-link"))
        tools.rmdir(os.path.join(self.package_folder, "SPIRV-Tools-opt"))
        tools.rmdir(os.path.join(self.package_folder, "SPIRV-Tools-reduce"))
        for bin_file in glob.glob(os.path.join(self.package_folder, "bin", "*SPIRV-Tools-shared.dll")):
            os.remove(bin_file)
        for lib_file in glob.glob(os.path.join(self.package_folder, "lib", "*SPIRV-Tools-shared*")):
            os.remove(lib_file)

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "SPIRV-Tools"
        self.cpp_info.names["cmake_find_package_multi"] = "SPIRV-Tools"
        self.cpp_info.names["pkg_config"] = "SPIRV-Tools"
        # SPIRV-Tools component
        self.cpp_info.components["spirv-tools-core"].names["cmake_find_package"] = "SPIRV-Tools"
        self.cpp_info.components["spirv-tools-core"].names["cmake_find_package_multi"] = "SPIRV-Tools"
        self.cpp_info.components["spirv-tools-core"].libs = ["SPIRV-Tools"]
        self.cpp_info.components["spirv-tools-core"].requires = ["spirv-headers::spirv-headers"]
        if self.settings.os == "Linux":
            self.cpp_info.components["spirv-tools-core"].system_libs.append("rt")
        if not self.options.shared and self._stdcpp_library:
            self.cpp_info.components["spirv-tools-core"].system_libs.append(self._stdcpp_library)
        # SPIRV-Tools-opt component
        self.cpp_info.components["spirv-tools-opt"].names["cmake_find_package"] = "SPIRV-Tools-opt"
        self.cpp_info.components["spirv-tools-opt"].names["cmake_find_package_multi"] = "SPIRV-Tools-opt"
        self.cpp_info.components["spirv-tools-opt"].libs = ["SPIRV-Tools-opt"]
        self.cpp_info.components["spirv-tools-opt"].requires = ["spirv-tools-core", "spirv-headers::spirv-headers"]
        # SPIRV-Tools-link component
        self.cpp_info.components["spirv-tools-link"].names["cmake_find_package"] = "SPIRV-Tools-link"
        self.cpp_info.components["spirv-tools-link"].names["cmake_find_package_multi"] = "SPIRV-Tools-link"
        self.cpp_info.components["spirv-tools-link"].libs = ["SPIRV-Tools-link"]
        self.cpp_info.components["spirv-tools-link"].requires = ["spirv-tools-opt"]
        # SPIRV-Tools-reduce component
        self.cpp_info.components["spirv-tools-reduce"].names["cmake_find_package"] = "SPIRV-Tools-reduce"
        self.cpp_info.components["spirv-tools-reduce"].names["cmake_find_package_multi"] = "SPIRV-Tools-reduce"
        self.cpp_info.components["spirv-tools-reduce"].libs = ["SPIRV-Tools-reduce"]
        self.cpp_info.components["spirv-tools-reduce"].requires = ["spirv-tools-core", "spirv-tools-opt"]

        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.path.append(bin_path)

    @property
    def _stdcpp_library(self):
        libcxx = self.settings.get_safe("compiler.libcxx")
        if libcxx in ("libstdc++", "libstdc++11"):
            return "stdc++"
        elif libcxx in ("libc++",):
            return "c++"
        else:
            return False

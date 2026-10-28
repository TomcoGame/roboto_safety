# SPDX-License-Identifier: GPL-3.0
# Builds the real inference node sources against fake motor and IMU drivers (fake_drivers.cpp).
# See README.md for how to run the safety behaviour test.

cmake_minimum_required(VERSION 3.16)
project(safety_sim CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

set(DEPLOY_SRC ${CMAKE_CURRENT_SOURCE_DIR}/../../src)
set(INF ${DEPLOY_SRC}/inference)
add_definitions(-DROOT_DIR=\"${INF}/\")

find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(spdlog REQUIRED)
find_package(fmt REQUIRED)

# ONNX Runtime and yaml-cpp, unpacked from the archives vendored in the inference package.
include(FetchContent)
FetchContent_Declare(onnxruntime
  URL ${INF}/thirdparty/onnxruntime-linux-x64-1.21.0.tgz
  URL_HASH SHA256=7485c7e7aac6501b27e353dcbe068e45c61ab51fbaf598d13970dfae669d20bf)
FetchContent_MakeAvailable(onnxruntime)
set(YAML_CPP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(YAML_CPP_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
FetchContent_Declare(yaml_cpp URL ${INF}/thirdparty/yaml-cpp-0.9.0.tar.gz)
FetchContent_MakeAvailable(yaml_cpp)

file(GLOB UTILS_SRC ${INF}/src/utils/*.cpp)
add_executable(safety_sim_node
  ${INF}/src/inference_node.cpp
  ${INF}/src/ros_interface.cpp
  ${INF}/src/obs_manager.cpp
  ${INF}/src/robot_interface.cpp
  ${UTILS_SRC}
  ${INF}/thirdparty/cnpy/cnpy.cpp
  fake_drivers.cpp)
target_include_directories(safety_sim_node PRIVATE
  ${INF}/src ${INF}/src/utils ${INF}/include ${INF}/thirdparty/cnpy
  ${DEPLOY_SRC}/motors/include ${DEPLOY_SRC}/motors/src
  ${DEPLOY_SRC}/imu/include
  ${onnxruntime_SOURCE_DIR}/include)
target_link_libraries(safety_sim_node
  ${onnxruntime_SOURCE_DIR}/lib/libonnxruntime.so yaml-cpp::yaml-cpp
  Eigen3::Eigen spdlog::spdlog fmt::fmt pthread z)
target_link_libraries(safety_sim_node
  rclcpp::rclcpp ${std_msgs_TARGETS} ${sensor_msgs_TARGETS} ${geometry_msgs_TARGETS} ${std_srvs_TARGETS})
set_target_properties(safety_sim_node PROPERTIES BUILD_RPATH ${onnxruntime_SOURCE_DIR}/lib)

cmake_minimum_required(VERSION 3.16)
project(adk_embedded_test_matrix C)

enable_testing()

add_library(adc_scale src/adc_scale.c)
target_include_directories(adc_scale PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

add_executable(test_adc_scale tests/test_adc_scale.c)
target_link_libraries(test_adc_scale PRIVATE adc_scale)

add_test(NAME adc_scale_host_unit COMMAND test_adc_scale)

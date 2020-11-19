add_library(sample1 SHARED sample1.cc)

install(TARGETS sample1 DESTINATION lib)

# test
add_executable(sample1_unittest sample1_unittest.cc)
target_link_libraries(sample1_unittest gtest gtest_main sample1)
add_test(sample1_unit sample1_unittest)

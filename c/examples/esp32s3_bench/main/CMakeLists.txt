idf_component_register(SRCS "bench.c" INCLUDE_DIRS "." "../../esp32s3_robot/main"
                       REQUIRES sparrow esp_timer EMBED_FILES "model.spb")

# Project configuration overrides (framework docs: build-system/configuration.md).
# DataProductsConfig.fpp: product buffers sized for the KissCam Image products (SDD §Data product).
register_fprime_config(
        DevicesReferenceConfig
    CONFIGURATION_OVERRIDES
        "${CMAKE_CURRENT_LIST_DIR}/DataProductsConfig.fpp"
    INTERFACE
)

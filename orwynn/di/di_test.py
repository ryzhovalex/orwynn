from pytest import fixture
from orwynn.boot.BootDataProxy import BootDataProxy
from orwynn.di.DI import DI
from orwynn.di.collecting.provider_dependencies_map import ProviderDependenciesMap
from orwynn.di.di_container import DIContainer
from orwynn.di.init.init_providers import init_providers


@fixture
def std_di_container(
    std_boot_data_proxy: BootDataProxy,
    std_provider_dependencies_map: ProviderDependenciesMap
) -> DIContainer:
    return init_providers(std_provider_dependencies_map)

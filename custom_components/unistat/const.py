"""Constants for the UniStat integration."""

from enum import StrEnum

DOMAIN = "unistat"

# General Purpose (used multiple forms)
CONF_TEMP_ENTITY = "temp_entity"
CONF_HUMIDITY_ENTITY = "humidity_entity"

# Main Settings
CONF_CONTROLS = "climate_controls"
CONF_AREAS = "areas"
CONF_CONTROL_MODE = "control_mode"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_ADJACENCY = "use_adjacency"
CONF_WEATHER_STATION = "use_weather_station"
CONF_WIND_SPEED_ENTITY = "wind_speed_entity"
CONF_WIND_DIRECTION_ENTITY = "wind_direction_entity"
CONF_SOLAR_FLUX_ENTITY = "solar_flux_entity"
CONF_GAS_PRICE_ENTITY = "gas_price_entity"
CONF_ELECTRIC_PRICE_ENTITY = "electric_price_entity"

# Appliance settings
CONF_APPLIANCE_TYPE = "appliance_type"
CONF_HEATING_POWER = "heating_power"
CONF_COOLING_POWER = "cooling_power"
CONF_APPLIANCE_METER = "appliance_meter"
CONF_SEER_RATING = "seer_rating"
CONF_SEER_STANDARD = "seer_version"
CONF_HSPF_RATING = "hspf_rating"
CONF_HSPF_STANDARD = "hspf_version"
CONF_EFFICIENCY = "efficiency"
CONF_CENTRAL_APPLIANCE = "central_appliance"

# Boiler Specific Settings
CONF_BOILER_INLET_TEMP_ENTITY = "boiler_inlet_temp"
CONF_BOILER_OUTLET_TEMP_ENTITY = "boiler_outlet_temp"


class ControlMode(StrEnum):
    """Thermostat Modes."""

    COMFORT = "Comfort"
    ECO = "Eco"
    BUDGET = "Budget"


class CentralApplianceType(StrEnum):
    """Appliance Types."""

    HydroBoiler = "HydroBoiler"
    HvacFurnace = "HVACFurnace"
    AcCompressor = "AcCompressor"
    HeatpumpCompressor = "HeatpumpCompressor"


class ControlApplianceType(StrEnum):
    """Appliance Types."""

    HeatpumpFanUnit = "HeatpumpFanUnit"
    BoilerZoneCall = "BoilerZoneCall"
    ThermoStaticRadiatorValve = "ThermoStaticRadiatorValve"
    HVACThermostat = "HVACThermostat"
    HVACHeatCall = "HVACHeatCall"
    HVACCoolCall = "HVACCoolCall"
    SpaceHeater = "SpaceHeater"
    WindowAC = "WindowAC"
    WindowHeatpump = "WindowHeatpump"


SWITCH_APPLIANCE_TYPES = [
    ControlApplianceType.BoilerZoneCall,
    ControlApplianceType.HVACCoolCall,
    ControlApplianceType.HVACHeatCall,
    ControlApplianceType.SpaceHeater,
    ControlApplianceType.WindowAC,
]
CLIMATE_APPLIANCE_TYPES = [
    ControlApplianceType.HVACThermostat,
    ControlApplianceType.HeatpumpFanUnit,
    ControlApplianceType.WindowHeatpump,
]

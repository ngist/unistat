# Github Custom for Home Assistant

[![Build][build_badge]][actions]
[![License][license_shield]](LICENSE)
[![hacs][hacs_badge]][hacs]

[license_shield]: https://img.shields.io/github/license/ngist/unistat?style=for-the-badge
[hacs]: https://github.com/custom-components/hacs
[hacs_badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[actions]: https://github.com/ngist/unistat/actions
[build_badge]: https://img.shields.io/github/actions/workflow/status/ngist/unistat/pythonpackage.yaml?branch=main&style=for-the-badge

> [!WARNING]
> This integration is in the very early statges of active development, it's not ready for use do not install!. See [Development Progress](#development-progress)

## About

This repo contains a custom component for [Home Assistant](https://www.home-assistant.io) that provides a unified thermostat control for your home.
It brings together all of your temp sensors and temperature control appliances for your house and can seamlessly control between them. The goal of this project is simplicity of setup and use. There shouldn't need to be any fiddling with control pramaters, and there's no option to do so either.

It also allows you to select between several different operating modes:

1.  Comfort: minimizes temperature fluctuations but may use more energy
2.  Budget: minimizes energy expenditure
3.  Eco: minimizes carbon footprint (if you only have one type of heating or cooling system this is the same as Budget mode)

## Motivation

Why bother making another thermostat integration?

I wanted a thermostat integration that would handle multi-room multi-appliance control optimization. UniStat uses an adaptive Model Predictive Control(MPC) algorithm to jointly optimize control outputs for all rooms simultaneously. This means if you have substantial heatflow from the first floor to the second floor(due to convection), it may reduce the amount of heat called for on the top floor because it knows a heatcall on the first floor will provide more optimal heating for both areas, sending a heatcall for both areas might otherwise result in overheating the second floor. Joint optimization should provide for lower energy use and better comfort than more naive approaches.

I also didn't want something that required manual fine tuning, and I wanted something that was relatively easy to setup and configure. I wanted a set it and forget it thermostat.

I looked at what was available and didn't see anything that checked these boxes.

- HA natively has thermostat helpers can't this all be done natively without a custom integration?

  I started with this but gave up quickly. If you have a relatively simple heating/cooling setup and it's well balanced for all the rooms you care about then using the built in thermostats may be a good option for you, but it became unmanagable for me. I have multiple heating appliances in each room(boiler/radiators and heatpumps) so these won't control between them so then automations are needed.

- Why not use [Versatile Thermostat](https://github.com/jmcollin78/versatile_thermostat) or [Better Thermostat](https://github.com/KartoffelToby/better_thermostat) or [HASmartThermostat](https://github.com/ScratMan/HASmartThermostat)?

  Well actually you may want to go check them out, and look at the [Features](#features) below to compare.

  Better and HASmartThermostat are both designed for working with a single room at a time, I want something that will manage multiple rooms elegantly especially when a heat or cooling call may cover more than one room at a time. Versatile has some functionality for managing multiple rooms but I don't think it handles multiple rooms on the same zone very well yet, additionally I don't think it can handle multiple heating appliances in the same room, I'll admit though there's a lot of documentation and it wasn't entirely clear to me what it could and couldn't do. Versatile and HASmartThermostat also require manual tuning of the control loops, this was something I wanted to avoid, especially given the interaction between rooms in my house it seemed like this would be a sisyphian task.

  I'll use my house as an example to make concrete the use case. I have a multizone boiler setup with open/closed zone valves but one zone is always on if any boiler zone is called(this prevents to possibility of the circulator pump driving into a closed system), I also have mini-split heatpumps in several rooms. I wanted a thermostat that would wisely choose between boiler heating and heatpump heating for any given room and ambient conditions, and also switch the heatpumps to cooling mode automatically when appropriate. At higher ambient temperatures the heatpumps are very efficient compared with the boiler but at much lower temperatures the heatumps either can't keep up in some rooms or are more costly to operate than the boiler, the goal is that this will use one or both heatsources as appropriate to maximize comfort and efficiency. Another problem I wanted to overcome is that basic on/off control of my boiler zones resulted in several degrees of overshoot so I wanted more optimal control, Versatile may solve this last issue but it would require fine tuning in all 9 of my rooms.

- What about xyz thermostat integration?

  At the time I started the project the above were the only ones I saw.

## Should I use this?

If you're in the situation where you have any of the following then this integration may be for you:

- You have a multi-zone heating or cooling system(s) where more than one area/temp sensor is in each zone.
- Partially overlapping heating/cooling zones, ie your heating zones aren't the same as your cooling zones.
- You have multiple heating or cooling systems for the same area. Maybe you have an HVAC system and a supplemental window AC unit, or you have a boiler/radiator system but you also have minisplit heat-pumps.

Supported control outputs:

- switch (for simple on/off heating/cooling/humidification/dehumidification calls)
- climate (for appliances that are already integrated into HA that have a climate interface)

## Features

### Roadmap

- [ ] Handle rooms with multiple heating/cooling appliances.
- [ ] Handle multiple rooms that are on the same heating or cooling zone
- [ ] Implement room adjacency for better control
- [ ] Use external temperature to optimize control
- [ ] Use boiler inlet/outlet temperatures to optimize control
- [ ] Implement comfort mode
- [ ] Implement budget mode
- [ ] Automatic tuning - no user configuration of control loop parameters everything is learned by mathemagic(or AI if you want to call it that).
- [ ] Implement better input validation on config options
- [ ] Implement presets
- [ ] Implement schedules
- [ ] Smart Start - activates heating or cooling early so temp is achieved by the scheduled time.
- [ ] Implement eco mode
- [ ] Use external wind speed and direction to optimize control
- [ ] Use solar irradiance to optimize control
- [ ] Implement stale sensor detection
- [ ] Implement freeze protection
- [ ] Implement inferred temperature for stale sensors
- [ ] Handle Grouped Mini-split heatpumps
- [ ] Implement TRV support

## Prerequisites

1. Setup [Areas](https://www.home-assistant.io/docs/organizing/areas/) for any room in your house you want this integration to control, or to have temperature readings for.
2. Have at least one temperature sensor in each Area you're interested in controlling, it doesn't need to be associated with the area in HA(though you probably should associate it), it just needs to be physically located there.
3. Have at least one climate control device controllable by HA, either switch or climate. You do not need to have a unique climate control device for every room. You can even have rooms which have no associated climate controls.

## Installation

The simplest way to install this integration is with the Home Assistant Community Store (HACS). This is not (yet) part of the default store and will need to be added as a custom repository.

## Configuration

The configuration flow centers around rooms and climate controls (or appliances). During the first step you will list the rooms and appliances to be configured and then will be prompted to setup each one.

### Main configuration

#### Rooms list:

During the first configuration step you will specify all indoor areas(rooms) that will be considered by UniStat, all of these rooms must have their own unique temperature sensor in them. If you have a room without a temperature sensor just leave it out regardless of whether it is controlled by a heating or cooling appliance.

#### Climate controls list:

These controls should each correspond to a unique climate control for your house, if you have a thermostat(climate entity) but also have access to directly control the heating/cooling calls you should not include both, the climate entity and the heating/cooling switch entities. You should choose one or the other, the heating or cooling calls are most likely preferable.

Some climate controls are associated with a central appliance, for instance you may have several boiler zone valves or TRVs but there's typically a single boiler that services all the zones, when you configure one of these appliances you'll be prompted to selected the associated central appliance or create a new one if it does not exist yet.

#### Weather entity:

The weather entity is required this is used to fetch the forecasted ambient outdoor temperatures for your house, so that it can anticipate the future heating and cooling demand. It is also used to provide other outdoor sensors for the current ambient conditions unless you check the option to use a local weather station then you can specify your own local sensors.

#### Energy price entities:

Energy prices are optional, if you only have one energy source then you can safely omit these, but if you have some electric and some gas heating then these are very important for budget mode, if you don't set them then budget mode won't really work effectively.

These are configured as entities rather than input values for two reasons.

- It allows for better reuse and maintenance in the event that you also use these values with utility meters to compute your spending. When rates change you only need to update one value.
- If you have a time of use plan on your electricity or some other dynamic pricing scheme, this allows it to be properly taken into account as utility rates change. Note: There unlike with temperature there is no look ahead on utility prices at each control cycle prices are assumed to be fixed at the current rate into the future.

### Adjacency

Specifying adjacency is optional. If you have a well balanced heating and cooling system, or only a central HVAC system you probably don't need to worry about this.

If not specified then all rooms are treated as not adjacent, this means the model assumes heatflow between them to be negligible. Situations that would break this assumption might be high temperature differentials between rooms.

Adjacency should be specified if there is significant heatflow between rooms.

> [!NOTE]  
> When configuring adjacency some rooms might be adjacent that are not obvious, remember a square room has 6 sides, the four walls plus the floor and ceiling. Additionally you may want to specify adjacency between rooms if you suspect there is the potential for significant heatflow between them even if they are not physically adjacent.

### Weather Station Config

Using a weather station is optional everything can be obtained from the weather forecast entity in the first step as such all these entities are optional.

If you want to use this integration without internet then you'll want to have at least the outside temperature or you want it to work well during sustained internet blackouts. Really all you need is temperature the others aren't currently used but may be some day.

### Room settings

For each room you specified in the first step you'll be propted to configure it's sensors.

Each room must have a unique temperature sensors, humidity is optional, but if specified it must also be unique to that room.

### Appliance settings

#### Terminology

##### Direct/Indirect

To properly configure the appliances it's important to define the concept of direct and indirect heating and cooling. Consider two room house the first room has a radiator in it and the second does not. The radiator directly heats the first room, and due to the fact that there is a relatively low thermal resistance between the rooms relative to the outside it indirectly heats the second room.

##### Standalone/Peripheral/Central Appliances

A control appliance can either be a **standalone appliance**, or a **peripheral appliance**. A **standalone appliance** is entirely contained in a room and directly affects only that room, a concrete example is an electric space heater. An example of a **peripheral appliance** would be a boiler zone call, it supplies heat to one or more rooms, but is dependent on a **central appliance**, the boiler. Central appliances are things like a furnace for an HVAC system, an AC compressor, or a Heatpump that supplies an HVAC system or multiple mini-splits.

#### Control Appliance configuration

You'll first need to select the appliance type, and what rooms it directly controls. The types available will depend on the underlying entity type. See the lists below for reference:

For switch entities:

- HVAC Cooling Call(Central)
- HVAC Heating Call(Central)
- BoilerZoneCall(Central)
- SpaceHeater(Room)
- WindowAC(Room)

For climate entities:

- HVACThermostat(Central)
- HeatpumpFanUnit(Central)
- WindowHeatpump(Room)

If a peripheral appliance has been specified you'll be prompted to specify the associated central appliance or add a new one.

If it's a standalone appliance you'll be prompted to enter information about it's heating or cooling capabilities and it's efficiency, all these should be obtainable from the sticker on the appliance.

Similarly if a central appliance needs to be configured you should be able to get all the info needed from the sticker on the appliance.

> [!NOTE]  
> Right now all efficiency numbers are based around SEER/SEER2, HSPF/HSPF2, and AFUE. These are US efficiency standards that appliance manufacturers in the US are required to put on their appliances. I'm happy to include other metrics based on other global standards if someone is willing to educate me.

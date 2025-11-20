# Github Custom for Home Assistant

[![](https://img.shields.io/github/license/ngist/ultrastat?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/github/actions/workflow/status/ngist/ultrastat/pythonpackage.yaml?branch=main&style=for-the-badge)](https://github.com/ngist/ultrastat/actions)

> [!WARNING]
> This integration is in the very early statges of active development, it's not ready for use do not install!. See [Development Progress](#development-progress)

## About

This repo contains a custom component for [Home Assistant](https://www.home-assistant.io) that provides the ultimate thermostat control for your home.
It brings together all of your temp sensors and temperature control appliances for your house and can seamlessly control between them.

It also allows you to select between several different modes:

1.  Comfort: minimizes temperature fluctuations but may use more energy
2.  Eco: minimizes carbon footprint
3.  Budget: minimizes energy expenditure (if you only have one type of heating or cooling this is the same as eco mode)

## Prerequisites

1. Setup [Areas](https://www.home-assistant.io/docs/organizing/areas/) for any room in your house you want this integration to control.
2. Have at least one temperature sensor in each Area your interested in controlling, it doesn't need to be associated with the area in HA(though you probably should associate it), it just needs to be physically located there.

## Installation

The simplest way to install this integration is with the Home Assistant Community Store (HACS). This is not (yet) part of the default store and will need to be added as a custom repository.

1. [Install HACS](https://hacs.xyz/docs/use/download/download/#to-download-hacs)
2. Go into HACS from the side bar.
3. Click into Integrations.
4. Click the 3-dot menu in the top right and select Custom repositories
5. In the UI that opens, copy and paste the url for this github repo into the Add custom repository URL field.
6. Set the category to Integration.
   Click the Add button.
   Select Emporia Vue from the list and press the download button.
   Further configuration is done within the Integrations configuration in Home Assistant. You may need to restart home assistant and clear your browser cache before it appears, try ctrl+shift+r if you don't see it in the configuration list.

## Motivation

You might wonder why bother making a thermostat integration, HA natively has thermostat helpers can't this all be done natively without a custom integration? Well yes it can, and in fact that's what I started with, well at least that's what I tried to do, but the complexity became unmanagable for my needs.

If you have a single zone HVAC system in your house the built in functionality in home assistant will work just fine for you, and you shouldn't bother with this integration. The simple thermostat integration provided will work nicely.

If you're in the situation where you have any of the following then this integration is for you:

- You have a multi-zone heating or cooling system(s) where more than one area/temp sensor is in each zone.
- Partially overlapping heating/cooling zones.
- You have multiple heating or cooling systems for the same area. Maybe you have an HVAC system and a supplemental window AC unit, or you have a boiler/radiator system but you also have minisplit heat-pumps.
- You have a single or multi-zone boiler system but simple on-off control of each zone results in too much over/undershoot.
- You have multiple mini-split heatpumps sharing the same condensor, and they can't operate in opposite modes.

Many of the above situations mean that you can't control one area at a time independently of the others. If one room is hot and another is cold and they are both on the same heating zone what do you do? Control to the average, minimum, maximum? Now what if you have an AC unit in the hot room, you don't want it to turn on in winter while you're heating, even if one of the rooms is warmer than desired. This makes for relatively complex control automations to implement from the UI, now imagine you have several zones, or maybe you have a heatpump in addition to the boiler, when do you use the boiler and when do you use the heatpump? The heatpump will generally be more efficient above a certain outside temperature, but if it's really cold you'll want to use the boiler to save money/energy.

A heatpump only supports one room at a time, but the boiler zone may cover several, from an energy efficiency standpoint it may be better to use the heatpump or the boiler, or both at the same time depending on which rooms need to be heated at any given time.

## Configuration

The configuration flow requires some explanation as many things are possible and supported that may not be obvious.

### Outdoor sensors

These are entirely optional, but populating at least outside temperature is recommended, for most people the other sensors will have minimal impact.

If you have a weather station you can use entities from this to populate outdoor sensors, if you don't have a weather station you can use a weather integration to provide these entities.

### Boiler settings

If you have a hydronic(aka water) boiler then you'll want to specify the heat call switch or switches if you have a multizone system. It's important for the system to know which controls are associated with the hydronic boiler as they have much longer time constants than HVAC type systems.

> [!Note]
> This integration assumes a hydronic boiler system with one or more heat call switches with one/off type zone valves, all valves are assumed to be normally closed. If you have a steam radiator system or you have flow reducing valves or an always circulating system with reset controller or some other exotic boiler system. These aren't supported right now. If you are interested in adding support drop me a note or open a PR.

### Room settings

You must specify what "area" these settings are for any entities that this integration makes will be added to these areas.

You must also specify a temperature sensor for the area, you can specify more than one if you like but you shouldn't need more than one. If you do specify more than one then the average reading is used for control. **Temperature sensors must be unique to each area, sharing temperature sensors across multiple areas is not allowed, because it's most likely a mistake.**

In general because a heating or cooling appliance or zone may cover more than one room, it is ok and even desirable to reuse these entities across multiple rooms to capture their association with those rooms.

Examples:
Scenario 1: The first floor is on a single boiler zone(switch.boiler_zone1) but you have three rooms with one temp sensors in each room. There are several options on how this could be configured. 1. (Preferred) You can setup 3 different areas each with it's own temp sensor, and use the same switch.boiler_zone1 for the heat call in all three. 2. (Not Recommended) You can setup a single area in UltraStat and add all three temp sensors to it.  
 3. (Not Recommended) You only really care about one room, so you only setup a single area in UltraStat and only supply the associated temp sensor for the room you care about.

        2 is not recommended as it provides less granular control, maybe you want to control to a different room at different times of day, option 2 doesn't allow for this. 3 omits information from UltraStat, which once adjacency information is added can help improve temperature control in the room you care about, you can just disable control in the rooms you aren't interested in after you setup UltraStat.

## Development Progress

- [x] Implement Configuration Flow
- [ ] Unit Test Configuration Flow
- [ ] Implement model learning
- [ ] Unit test model learning
- [ ] Implement comfort control
- [ ] Unit test comfort control

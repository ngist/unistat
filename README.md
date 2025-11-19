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

## Development Progress

- [x] Implement Configuration Flow
- [ ] Unit Test Configuration Flow
- [ ] Implement model learning
- [ ] Unit test model learning
- [ ] Implement comfort control
- [ ] Unit test comfort control

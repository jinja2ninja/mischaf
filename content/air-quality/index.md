---
archetype: "chapter"
weight: 1
aliases: ["posts", "articles", "blog", "showcase", "docs"]
title: "Air Quality"
author: "Mischa Friegang"
tags: ["index"]
_build:
  list: false
---
<div class="widget-container">
  <div class="widget-wrapper">
    <h3 class="widget-title">Garden Valley</h3>
    <div id='PurpleAirWidget_83261_module_AQI_conversion_C0_average_10_layer_standard' class="widget">Loading PurpleAir Widget...</div>
  </div>
  <div class="widget-wrapper">
    <h3 class="widget-title">Georgetown</h3>
    <div id='PurpleAirWidget_81519_module_AQI_conversion_C0_average_10_layer_standard' class="widget">Loading PurpleAir Widget...</div>
  </div>
  <div class="widget-wrapper">
    <h3 class="widget-title">Placerville</h3>
    <div id='PurpleAirWidget_149960_module_AQI_conversion_C0_average_10_layer_standard' class="widget">Loading PurpleAir Widget...</div>
  </div>
  <div class="widget-wrapper">
    <h3 class="widget-title">South Lake Tahoe</h3>
    <div id='PurpleAirWidget_65909_module_AQI_conversion_C0_average_10_layer_standard' class="widget">Loading PurpleAir Widget...</div>
  </div>
</div>

<script src='https://www.purpleair.com/pa.widget.js?key=7U882MCGDP3UAEHM&module=AQI&conversion=C0&average=10&layer=standard&container=PurpleAirWidget_83261_module_AQI_conversion_C0_average_10_layer_standard'></script>
<script src='https://www.purpleair.com/pa.widget.js?key=LTLW3KJBY199B6CK&module=AQI&conversion=C0&average=10&layer=standard&container=PurpleAirWidget_81519_module_AQI_conversion_C0_average_10_layer_standard'></script>
<script src='https://www.purpleair.com/pa.widget.js?key=TD3HTHHLSHZ1OAJR&module=AQI&conversion=C0&average=10&layer=standard&container=PurpleAirWidget_149960_module_AQI_conversion_C0_average_10_layer_standard'></script>
<script src='https://www.purpleair.com/pa.widget.js?key=PB6DXSH1W5AOBBYW&module=AQI&conversion=C0&average=10&layer=standard&container=PurpleAirWidget_65909_module_AQI_conversion_C0_average_10_layer_standard'></script>
<style>
  .widget-container {
    display: flex;
    justify-content: space-between;
  }
  .widget-wrapper {
    flex: 1;
    margin-right: 20px;
  }
  .widget-wrapper:last-child {
    margin-right: 0;
  }
  .widget-title {
    margin-top: 0;
    text-align: center;
  }
  .widget {
    border: 1px solid #ccc;
    padding: 10px;
  }
</style>

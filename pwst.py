#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#       pwst.py
#       
#       Copyright 2011 Cilyan Olowen <gaknar@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import pygtk
pygtk.require("2.0")
import gtk

import dbus
from dbus.mainloop.glib import DBusGMainLoop

import datetime

class UPowerInterface:
  def __init__(self, power_status):
    self.bus = dbus.SystemBus()
    self.upower_ob = self.bus.get_object("org.freedesktop.UPower",
                                         "/org/freedesktop/UPower")
    self.upower = dbus.Interface(self.upower_ob, "org.freedesktop.UPower")
    self.power_status = power_status
    self.find_batteries()
    self.select_battery(self.batteries[0])
    self.update()
  
  def find_batteries(self):
    devices = self.upower.EnumerateDevices()
    self.batteries = []
    for device in devices:
      proxy = self.bus.get_object("org.freedesktop.UPower",device)
      iface = dbus.Interface(proxy, dbus.PROPERTIES_IFACE)
      dtype = iface.Get("org.freedesktop.UPower.Device", "Type")
      if dtype == 2L:
        self.batteries.append(device.__str__())
  
  def select_battery(self,battery):
    print("Using %s"%(battery))
    self.battery_ob = self.bus.get_object("org.freedesktop.UPower",battery)
    self.battery_prop = dbus.Interface(self.battery_ob, dbus.PROPERTIES_IFACE)
    self.battery = dbus.Interface(self.battery_ob, "org.freedesktop.UPower.Device")
    self.battery.connect_to_signal("Changed", self.update)
  
  def update(self):
    percent = self.battery_prop.Get("org.freedesktop.UPower.Device",
                                    "Percentage")
    state = self.battery_prop.Get("org.freedesktop.UPower.Device",
                                  "State")
    charge = False
    if state == 1L or state == 4L:
      charge = True
    
    if charge:
      time = self.battery_prop.Get("org.freedesktop.UPower.Device",
                                   "TimeToFull")
    else:
      time = self.battery_prop.Get("org.freedesktop.UPower.Device",
                                   "TimeToEmpty")
    rest_time = datetime.timedelta(seconds=int(time))
    self.power_status.set_power_status(int(percent), charge, str(rest_time))

class PowerStatus(gtk.StatusIcon):
  def __init__(self):
    gtk.StatusIcon.__init__(self)
    self.set_visible(True)
    self.menu = gtk.Menu()
    self.menu_item_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
    self.menu_item_quit.connect("activate", self.destroy)
    self.menu_item_quit.show()
    self.menu.append(self.menu_item_quit)
    self.connect("popup-menu", self.popup_menu)
  
  def popup_menu(self, status_icon, button, activate_time):
    self.menu.popup(None, None, None, button, activate_time, None)
  
  def destroy(self,widget):
    self.set_visible(False)
    gtk.main_quit()
  
  def set_power_status(self,percent,charging,rest_time):
    base_name = "gpm-battery-"
    level = "000"
    if percent > 10:
      level = "020"
    if percent > 30:
      level = "040"
    if percent > 50:
      level = "060"
    if percent > 70:
      level = "080"
    if percent > 90:
      level = "100"
    charge = ""
    msg_tip = "Décharge : %d%%\nTemps restant : %s"
    if charging == True:
      charge = "-charging"
      msg_tip = "En charge: %d%%\nTemps avant charge complète : %s"
    self.set_from_icon_name(base_name + level + charge)
    self.set_tooltip_text(msg_tip%(percent,rest_time))

def main():
  DBusGMainLoop(set_as_default=True)
  ps = PowerStatus()
  up = UPowerInterface(ps)
  gtk.main()
  return 0

if __name__ == '__main__':
  main()
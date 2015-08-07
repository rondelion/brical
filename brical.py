#!/usr/bin/env python
# -*- coding: utf-8 -*-

# BriCA Language Interpreter for V1 (Interpreter version 0)
#  Originally licenced for WBAI (wbai.jp) under the Apache License (?)
#  Created: 2015-07-18

# TODO: submodules, name spaces, subports

import sys
import numpy
import brica1
import json

class LanguageInterpreter:
    __unit_dic={}	# 辞書：BriCA ユニット名⇒ユニットオブジェクト
    __jsn = None	# json オブジェクト
    __super_modules={}	# 上位モジュール

    def __init__(self):
        """ Create a new `LanguageInterpreter` instance.

        Args:
          None.

        Returns:
          LanguageInterpreter: a new `LanguageInterpreter` instance.

        """
        __unit_dic={}
        __super_modules={}

    def load_file(self, file_object):
        """ Load a BriCA language json file.

        Args:
          A file object

        Returns:
          A module dictionary: {module name, unit instance} pairs

        """
	self.__jsn = json.load(file_object)
	self.__add_modules()
	self.__add_ports()
	self.__add_connections()
	return self.__unit_dic

    def create_agent(self, scheduler):
        """ Add top level modules to a BriCA agent (to be called after load_file).

        Args:
          A brica1.Scheduler object

        Returns:
          A BriCA agent

        """
	top_module = brica1.Module()
	for unit_key in self.__unit_dic.keys():
	    if not unit_key in self.__super_modules:
		if isinstance(self.__unit_dic[unit_key], brica1.Component):
		    top_module.add_component(unit_key, self.__unit_dic[unit_key])
		    print "Adding a component " + unit_key + " to a BriCA agent."
		elif isinstance(self.__unit_dic[unit_key], brica1.Module):
		    top_module.add_submodule(unit_key, self.__unit_dic[unit_key])
		    print "Adding a module " + unit_key + " to a BriCA agent."
	agent = brica1.Agent(scheduler)
	agent.add_submodule("__Runtime_Top_Module", top_module)
	return agent

    def __add_modules(self):
        """ Add modules from the JSON description
        Args:
          None
        Returns:
          None
        """
        modules = self.__jsn["Modules"]
        for module in modules:
            self.__add_a_module(module)

    def __add_a_module(self, module):
    	if "ImplClass" in module:
    	    # if an implementation class is specified
    	    print "Use the existing ImplClass " + module["ImplClass"] + " for " + module["Name"] + "."
    	    try:
		self.__unit_dic[module["Name"]]=eval(module["ImplClass"]+'()')
		# New ImplClass instance
    	    except:
		print >> sys.stderr, "Component " + module["ImplClass"] + " not found for " +  module["Name"] + "!"
		self.__unit_dic[module["Name"]]=brica1.Module()	# New Module instance
	elif module["Name"] in self.__unit_dic:
	    pass	# TODO: Merge module properties
	else:		# No pre-existing unit with the same name
	    print "Create a new module instance"
	    self.__unit_dic[module["Name"]]=brica1.Module()		# New Module instance
	if "SuperModule" in module:
	    if module["SuperModule"].strip() != "":
		self.__super_modules[module["Name"]]=module["SuperModule"]
		if module["SuperModule"] in self.__unit_dic:
		    if isinstance(self.__unit_dic[module["Name"]], brica1.Component):
			self.__unit_dic[module["SuperModule"]].add_component(module["Name"], self.__unit_dic[module["Name"]])
			print "Adding a component " + module["Name"] + " to " + module["SuperModule"] + "."
		    elif isinstance(self.__unit_dic[unit_key], brica1.Module):
			self.__unit_dic[module["SuperModule"]].add_submodule(module["Name"], self.__unit_dic[module["Name"]])
			print "Adding a module " + module["Name"] + " to " + module["SuperModule"] + "."
		else:
		    print "SuperModule " + module["SuperModule"] + "has not been defined."
	if "SubModules" in module:
	    for submodule in module["SubModules"]:
		self.__super_modules[submodule]=module["Name"]
		if submodule in self.__unit_dic:
		    if isinstance(self.__unit_dic[submodule], brica1.Component):
			self.__unit_dic[module["Name"]].add_component(submodule, self.__unit_dic[submodule])
			print "Adding a component " + submodule + " to " + module["Name"] + "."
		    elif isinstance(self.__unit_dic[unit_key], brica1.Module):
			self.__unit_dic[module["Name"]].add_submodule(submodule, self.__unit_dic[submodule])
			print "Adding a module " + submodule + " to " + module["Name"] + "."
		else:
		    print "SubModule " + submodule + "has not been defined."

    def __add_ports(self):
        """ Add ports from the JSON description

        Args:
          None

        Returns:
          None

        """
        ports = self.__jsn["Ports"]
        for port in ports:
            self.__add_a_port(port)

    def __add_a_port(self, port):
	port_module = port["Module"]	# TODO: "Unit"?
	port_type = port["Type"]
	port_name = port["Name"]
	dimension = port["Dimension"]
	try:
	    length = 1
	    for i in dimension:
		length=length*i
	    if length < 1:
		raise ValueError("Port dimension < 1!")
	    if port_module in self.__unit_dic:
		module=self.__unit_dic[port_module]
		if port_type == "Input":
		    module.make_in_port(port_name, length)
		    print "Creating an input port " + port_name + " with the length " + str(length) + " to " + port_module + "."
		elif port_type == "Output":
		    module.make_out_port(port_name, length)
		    print "Creating an output port " + port_name + " with the length " + str(length) + " to " + port_module + "."
		else:
		    print >> sys.stderr, "Invalid port type!"
	    else:
		print >> sys.stderr, "Module " + port_module + " not found!"
	except IndexError:
	    print >> sys.stderr, "Dimension error for the port " + port_name + "!"
	except ValueError:
	    print >> sys.stderr, "Dimension error for the port " + port_name + "!"
	except:
	    print >> sys.stderr, "Error creating a port " + port_name + " with the length " + str(length) + " to " + port_module + "."

    def __add_connections(self):
        """ Add connections from the JSON description

        Args:
          None

        Returns:
          None

        """
        connections = self.__jsn["Connections"]
        for connection in connections:
            self.__add_a_connection(connection)

    def __add_a_connection(self, connection):
	# TODO: Port length check
	connection_name = connection["Name"]
	from_unit = connection["FromModule"]
	from_port = connection["FromPort"]
	to_unit = connection["ToModule"]
	to_port = connection["ToPort"]
	# Checking if the modules have been defined.
	if not from_unit in self.__unit_dic:
	    msg = "Module " + from_unit + " not defined!"
	    raise KeyError(msg)
	    return
	if not to_unit in self.__unit_dic:
	    msg = "Module " + to_unit + " not defined!"
	    raise KeyError(msg)
	    return
	# if from_unit & to_unit belong to the same level
	if (not from_unit in self.__super_modules) and (not to_unit in self.__super_modules):
	    print "No super modules for " + from_unit + " and " + to_unit + "."
	    
	if ((not from_unit in self.__super_modules) and (not to_unit in self.__super_modules)) or \
	(from_unit in self.__super_modules and to_unit in self.__super_modules and (self.__super_modules[from_unit] == self.__super_modules[to_unit])):
	    try:
		self.__unit_dic[from_unit].get_out_port(from_port)	# TODO: Name Space
		self.__unit_dic[to_unit].get_in_port(to_port)		# TODO: Name Space
	    except KeyError:
		print >> sys.stderr, "Error adding a connection from " + from_unit + " to " + to_unit + " on the same level but not from an output port to an input port!"
		return
	    # Creating a connection
	    brica1.connect((self.__unit_dic[from_unit],from_port), (self.__unit_dic[to_unit],to_port))
	    print "Creating a connection from " + from_port + " of " + from_unit + " to " + to_port + " of " + to_unit + "."
	# else if from_unit is the direct super module of the to_unit
	elif to_unit in self.__super_modules and self.__super_modules[to_unit]==from_unit:
	    try:
		self.__unit_dic[from_unit].get_in_port(from_port)	# TODO: Name Space
		self.__unit_dic[to_unit].get_in_port(to_port)		# TODO: Name Space
	    except KeyError:
		print >> sys.stderr, "Error adding a connection from the super module " + from_unit + " to " + to_unit + " but not from an input port to an input port!"
		return
	    # Creating a connection (alias)
	    self.__unit_dic[to_unit].alias_in_port(self.__unit_dic[from_unit], from_port, to_port)
	    print "Creating a connection (alias) from " + from_port + " of " + from_unit + " to " + to_port + " of " + to_unit + "."
	# else if to_unit is the direct super module of the from_unit
	elif from_unit in self.__super_modules and self.__super_modules[from_unit]==to_unit:
	    try:
		self.__unit_dic[from_unit].get_out_port(from_port)	# TODO: Name Space
		self.__unit_dic[to_unit].get_out_port(to_port)		# TODO: Name Space
	    except KeyError:
		print >> sys.stderr, "Error adding a connection from " + from_unit + " to its super module " + to_unit + " but not from an output port to an output port!"
		return
	    # Creating a connection (alias)
	    self.__unit_dic[from_unit].alias_out_port(self.__unit_dic[to_unit], to_port, from_port)
	    print "Creating a connection (alias) from " + from_port + " of " + from_unit + " to " + to_port + " of " + to_unit + "."
	# else connection level error!
	else:
	    msg = "Trying to add a connection between units " + from_unit + " and " + to_unit + " in a remote level!"
	    raise KeyError(msg)
	    return

# TODO: Link Check
## All ports are defined?
## All modules are grounded as components?
## Port dimensions matches?
print "BriCAL.py loaded!"

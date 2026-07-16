# ================================================================
# TIMING SCHEMA
# ================================================================

TIMING_SCHEMA = {

    "startpoint": "",

    "endpoint": "",

    "arrival_time": 0.0,

    "required_time": 0.0,

    "delay": 0.0,

    "slack": 0.0,

    "status": "",

    "violation_type": "",

    "cells": [],

    "clock_domain": "",

    "path_group": ""
}


# ================================================================
# CREATE EMPTY TIMING ENTRY
# ================================================================

def create_timing_entry():

    return TIMING_SCHEMA.copy()
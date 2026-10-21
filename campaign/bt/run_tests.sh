#!/bin/bash
cd "$(dirname "$0")/../.." && python3 -m pytest campaign/bt/tests/ -q

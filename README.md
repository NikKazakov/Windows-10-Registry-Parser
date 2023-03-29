# Windows-10-Registry-Parser

## Intro
Provides generalized classes for parsing Windows 10 registry.
Contains low-level parsing classes and a couple classes for exposing keys and values at high-level. Distinguishing features are:
 - lazy-loading - we try our best to only load stuff when it's called either by user or by related data
 - properties - everything is exposed as a property (and via some __getattribute__ magic)
 - iterables - list objects implement iter and next method, so they can be used both in loops and by indices

## Usage
see main.py for basic usage

## TODO
KeySecurity cell type\
Other REG_ data types

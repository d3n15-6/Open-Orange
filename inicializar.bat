@echo off
if NOT exist local\Company.data copy local\Company.data.example local\Company.data
if NOT exist local\LocalSettings.data copy local\LocalSettings.data.example local\LocalSettings.data
if NOT exist local\DocumentPrinter.data copy local\DocumentPrinter.data.example local\DocumentPrinter.data
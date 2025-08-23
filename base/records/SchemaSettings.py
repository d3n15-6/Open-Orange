#encoding: utf-8
from OpenOrange import *

ParentSchemaSettings = SuperClass('SchemaSettings','Setting',__file__)
class SchemaSettings(ParentSchemaSettings):
    buffer = SettingBuffer()

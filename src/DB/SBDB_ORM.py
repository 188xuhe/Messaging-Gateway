# coding: utf-8
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship,backref
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class Account(Base):
    __tablename__ = u'account'

    # user roles
    USER = 100
    ADMIN = 300
    
    id = Column(Integer, primary_key=True)
    language_id = Column(ForeignKey(u'language.id'), nullable=False)
    user_name = Column(String(20))
    password = Column(String(50))
    email = Column(String(255))
    mobile_phone = Column(String(50))
    version = Column(Integer)
    role = Column(Integer, default=USER)

    language = relationship(u'Language')

    
class Alarm(Base):
    __tablename__ = u'alarm'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(ForeignKey(u'event.id'), nullable=False)
    apartment_device_id = Column(ForeignKey(u'apartment_device.id'), nullable=False)
    
    event = relationship(u'Event',backref=backref('alarms', order_by=id))
    apartment_device = relationship(u'ApartmentDevice',backref=backref('alarms', order_by=id))


class AlarmName(Base):
    __tablename__ = u'alarm_name'

    language_id = Column(ForeignKey(u'language.id'), primary_key=True, nullable=False)
    device_type_id = Column(ForeignKey(u'device_type.id'), primary_key=True, nullable=False)
    name = Column(String(50))

    device_type = relationship(u'DeviceType')
    language = relationship(u'Language')
    
class Apartment(Base):
    __tablename__ = u'apartment'

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(ForeignKey(u'account.id'), nullable=False)
    name = Column(String(50))
    arm_state = Column(Integer)
#    scene_id = Column(ForeignKey(u'scene.id'))
    scene_id = Column(Integer)
    dt_arm = Column(DateTime)
    version = Column(Integer)

    account = relationship(u'Account',backref=backref('apartments', order_by=id))
#    scene = relationship(u'Scene', primaryjoin='Apartment.scene_id == Scene.id')

class ApartmentDevice(Base):
    __tablename__ = u'apartment_device'

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(ForeignKey(u'device.id'))
    apartment_id = Column(ForeignKey(u'apartment.id'))
    superbox_id = Column(Integer)
    name = Column(String(50))
#     flag_notification = Column(String(32))

    device = relationship(u'Device',backref="apartment_devices")
    apartment = relationship(u'Apartment',backref="apartment_devices",lazy='joined')
    
    
class ApartmentDeviceKey(Base):
    __tablename__ = u'apartment_device_key'

    id = Column(Integer, primary_key=True)
    apartment_device_id = Column(ForeignKey(u'apartment_device.id'))
    device_key_code_id = Column(ForeignKey(u'device_key_code.id'))
    name = Column(String(50))

    apartment_device = relationship(u'ApartmentDevice',backref="apartment_device_keys")
    device_key_code = relationship(u'DeviceKeyCode',backref="apartment_device_keys")


class Apartment_Superbox(Base):
    __tablename__ = u'apartment_superbox'

    apartment_id = Column(Integer,ForeignKey(u'apartment.id'), primary_key=True)
    superbox_id = Column(Integer,ForeignKey(u'superbox.id'), primary_key=True)
    name = Column(String(50))

    apartment = relationship(u'Apartment',backref=backref('apartment_superboxs', order_by=superbox_id))
    superbox = relationship(u'Superbox',backref=backref('apartment_superboxs', order_by=apartment_id))


class Client(Base):
    __tablename__ = u'client'

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(ForeignKey(u'account.id'), nullable=False)
    device_token = Column(String(100))
    enable_alarm = Column(Boolean)
    os = Column(String(50))
    dt_auth=Column(DateTime)
    dt_active=Column(DateTime)
    server_id=Column(Integer)
    terminal_code = Column(String(50))

    account = relationship(u'Account',backref="clients")


class Contactor(Base):
    __tablename__ = u'contactor'

    id = Column(Integer, primary_key=True, index=True)
    apartment_id = Column(ForeignKey(u'apartment.id'), nullable=False)
    name = Column(String(50))
    mobile_phone = Column(String(50))
    email_addr = Column(String(200))

    apartment = relationship(u'Apartment',backref="contactors")


class Device(Base):
    __tablename__ = u'device'

    id = Column(Integer, primary_key=True, index=True)
    device_model_id = Column(ForeignKey(u'device_model.id'), nullable=False)
#    superbox_id = Column(ForeignKey(u'superbox.id'), nullable=False)
    uni_code = Column(String(50))
#     name = Column(String(50))
#     flag_notification = Column(String(32))

    device_model = relationship(u'DeviceModel',backref="devices")
#    superbox = relationship(u'Superbox',backref="devices")


class DeviceCmd(Base):
    __tablename__ = u'device_cmd'

    id = Column(Integer, primary_key=True)
    device_key_id = Column(ForeignKey(u'device_key.id'))
    value = Column(Integer)
    name = Column(String(50))

    device_key = relationship(u'DeviceKey',backref="device_cmds")


class DeviceKey(Base):
    __tablename__ = u'device_key'

    id = Column(Integer, primary_key=True)
    device_model_id = Column(ForeignKey(u'device_model.id'), nullable=False)
    seq = Column(Integer)
    name = Column(String(50))
    can_enum = Column(Boolean)
    max_state_value = Column(Integer)
    min_state_value = Column(Integer)
    alarm_type = Column(Integer)

    device_model = relationship(u'DeviceModel',backref="device_keys")


class Event(Base):
    __tablename__ = u'event'

    id = Column(Integer, primary_key=True, index=True)
    device_key_code_id = Column(ForeignKey(u'device_key_code.id'))
    #device_uni_code = Column(String(50))
    value = Column(Integer)
    dt = Column(DateTime)
    alarm_level = Column(Integer)

    device_key_code = relationship(u'DeviceKeyCode')
    


class DeviceKeyCode(Base):
    __tablename__ = u'device_key_code'

    id = Column(Integer, primary_key=True)
    device_id = Column(ForeignKey(u'device.id'), nullable=False)
    device_key_id = Column(ForeignKey(u'device_key.id'), nullable=False)
    key_code = Column(String(50))
#    name = Column(String(50))

    device = relationship(u'Device',backref="device_key_codes")
    device_key = relationship(u'DeviceKey',backref="device_key_codes")


class DeviceModel(Base):
    __tablename__ = u'device_model'

    id = Column(Integer, primary_key=True, index=True)
    device_type_id = Column(ForeignKey(u'device_type.id'))
    name = Column(String(50))

    device_type = relationship(u'DeviceType',backref="device_models")


class DeviceState(Base):
    __tablename__ = u'device_state'

    id = Column(Integer, primary_key=True, index=True)
    device_key_id = Column(ForeignKey(u'device_key.id'), nullable=False)
    value_begin = Column(Integer)
    value_end = Column(Integer)
    name = Column(String(50))
    alarm_level = Column(Integer)

    device_key = relationship(u'DeviceKey',backref="device_states")


class DeviceType(Base):
    __tablename__ = u'device_type'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))


class Language(Base):
    __tablename__ = u'language'

    id = Column(Integer, primary_key=True, index=True)
    language = Column(String(50))


class MessageTemplate(Base):
    __tablename__ = u'message_template'

    id = Column(Integer, primary_key=True, index=True)
    language_id = Column(ForeignKey(u'language.id'), index=True)
    account_id = Column(ForeignKey(u'account.id'))
    sensor_model_id = Column(ForeignKey(u'device_model.id'))
    template = Column(String(50))

    account = relationship(u'Account',backref="MessageTemplates")
    language = relationship(u'Language',backref="MessageTemplates")
    sensor_model = relationship(u'DeviceModel',backref="MessageTemplates")


class Param(Base):
    __tablename__ = u'param'

    param_name = Column(String(500), primary_key=True)
    param_value = Column(String(5000))


class RestoreRequire(Base):
    __tablename__ = u'restore_require'

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(ForeignKey(u'account.id'), nullable=False)
    dt = Column(DateTime)
    uuid = Column(String(50))
    finished = Column(Boolean)

    account = relationship(u'Account',backref="RestoreRequires")

class Server(Base):
    __tablename__ = u'server'

    id = Column(Integer, primary_key=True)
    type = Column(Integer)
    address =Column(String(50))
    extern_address=Column(String(50))
    status =Column(String(50))
    dt_active=Column(DateTime)

class Scene(Base):
    __tablename__ = u'scene'

    id = Column(Integer, primary_key=True)
    apartment_id = Column(ForeignKey(u'apartment.id'), nullable=False)
    name = Column(String(50))

    apartment = relationship(u'Apartment', primaryjoin='Scene.apartment_id == Apartment.id',backref="scenes")


class SceneContent(Base):
    __tablename__ = u'scene_content'

    id = Column(Integer, primary_key=True)
    scene_id = Column(ForeignKey(u'scene.id'), nullable=False)
    device_key_code_id = Column(ForeignKey(u'device_key_code.id'), nullable=False)
    value = Column(Integer)

    device_key_code = relationship(u'DeviceKeyCode')
    scene = relationship(u'Scene',backref="scene_contents")


class SmsSenderHead(Base):
    __tablename__ = u'sms_sender_head'

    id = Column(Integer, primary_key=True, index=True)
    apartment_id = Column(ForeignKey(u'apartment.id'), nullable=False)
    content = Column(String(256))
    dt = Column(DateTime)

    apartment = relationship(u'Apartment')


class SmsSenderList(Base):
    __tablename__ = u'sms_sender_list'

    id = Column(Integer, primary_key=True, index=True)
    head_id = Column(ForeignKey(u'sms_sender_head.id'), nullable=False)
    mobile_phone = Column(String(50))
    result = Column(Integer)

    head = relationship(u'SmsSenderHead',backref="sms_sender_lists")


class Superbox(Base):
    __tablename__ = u'superbox'

    id = Column(Integer, primary_key=True, index=True)
    uni_code = Column(String(50))
    dt_auth=Column(DateTime)
    dt_active=Column(DateTime)
    server_id=Column(Integer)
    
    
    

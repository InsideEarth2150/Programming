#!/usr/bin/env python3
from enum import Enum, unique
from io import StringIO
from itertools import groupby

import csv
import os
import os.path
import sys


usage = '''par2csv.py [parfile]
This script will decompile the specified PAR file (EARTH2150.par in the current directory by default) and dump its contents to a series of CSV files in the current directory.\
'''

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'EARTH2150.par'

def read_int(stream):
    return int.from_bytes(stream.read(4), byteorder='little')

def read_string(stream):
    length = read_int(stream)
    namedata = stream.read(length)
    try:
        return namedata.decode(encoding='latin_1')
    except:
        print(length, namedata)
        raise

def read_field(stream, is_string):
    if is_string:
        return read_string(stream)
    else:
        return read_int(stream)


class Faction(Enum):
    NEUTRAL = 0
    UCS = 1
    ED = 2
    LC = 3

    def __str__(self):
        return self.name


class EntityType(Enum):
    Vehicle = 1
    Cannon = 2
    Missile = 3
    Building = 4
    Special = 5
    Equipment = 6
    ShieldGenerator = 7
    SoundPack = 8
    SpecialUpdatesLinks = 9
    Parameters = 10


class ResearchTab(Enum):
    CHASSIS = 0
    WEAPON = 1
    AMMO = 2
    SPECIAL = 3

    def __str__(self):
        return self.name


@unique
class EntityClass(Enum):
    # Vehicle
    VEHICLE              = 0x00c00101
    #MOVEABLE             = 0x00c00101
    SUPPLYTRANSPORTER    = 0x01c00101
    BUILDROBOT           = 0x02c00101
    MININGROBOT          = 0x04c00101
    SAPPERROBOT          = 0x08c00101
    # Cannon
    CANNON               = 0x00000102
    # Missile
    MISSILE              = 0x00010401
    # Building
    BUILDING             = 0x00010101
    # Special
    PASSIVE              = 0x00000201
    MINE                 = 0x00000801
    MULTIEXPLOSION       = 0x00010004
    BUILDPASSIVE         = 0x00010201
    PLATOON              = 0x00020101
    TRANSIENTPASSIVE     = 0x00020201
    EXPLOSION            = 0x00020401
    FLYINGWASTE          = 0x00040401
    UPGRADECOPULA        = 0x00001002
    STARTINGPOSITIONMARK = 0x00080101
    SMOKE                = 0x00080401
    ARTEFACT             = 0x01020201
    EXPLOSIONEX          = 0x01020401
    BUILDINGTRANSPORTER  = 0x01040101
    WALLLASER            = 0x01100401
    RESOURCETRANSPORTER  = 0x02040101
    BUILDERLINE          = 0x02100401
    UNITTRANSPORTER      = 0x04040101
    # Equipment
    EQUIPMENT            = 0x00000002
    REPAIRER             = 0x00000202
    CONTAINERTRANSPORTER = 0x00000402
    LOOKROUNDEQUIPMENT   = 0x00000802
    TRANSPORTERHOOK      = 0x00002002

    def __repr__(self):
        return self.name


type_field_map = {
    EntityType.Vehicle: ['classID', 'mesh', 'shadowType', 'viewParamsIndex', 'cost', 'timeOfBuild', '$soundPackID', '$smokeID', '$killExplosionID', '$destructedID', 'hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'sightRange', '$talkPackID', '$shieldGeneratorID', 'maxShieldUpdate', 'slot1Type', 'slot2Type', 'slot3Type', 'slot4Type', 'soilSpeed', 'roadSpeed', 'sandSpeed', 'bankSpeed', 'waterSpeed', 'deepWaterSpeed', 'airSpeed', 'objectType', '$engineSmokeID', '$dustID', '$billowID', '$standBillowID', '$trackID'],
    EntityType.Cannon: ['classID', 'mesh', 'shadowType', 'viewParamsIndex', 'cost', 'timeOfBuild', '$soundPackID', '$smokeID', '$killExplosionID', '$destructedID', 'rangeOfSight', 'plugType', 'slotType', 'maxAlphaPerTick', 'maxBetaPerTick', 'alphaMargin', 'betaMargin', 'barrelBetaType', 'barrelBetaAngle', 'barrelCount', '$ammoID', 'ammoType', 'targetType', 'rangeOfFire', 'plusDamage', 'fireType', 'shootDelay', 'needExternal', 'reloadDelay', 'maxAmmo', '$barrelExplosionID'],
    EntityType.Missile: ['classID', 'mesh', 'shadowType', 'viewParamsIndex', 'cost', 'timeOfBuild', '$soundPackID', '$smokeID', '$killExplosionID', '$destructedID', 'hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'resistantFlags', 'standType', 'type', 'rocketType', 'missileSize', '$rocketDummyID', 'IsAntiRocketTarget', 'speed', 'timeOfShoot', 'plusRangeOfFire', 'hitType', 'hitRange', 'typeOfDamage', 'damage', '$explosionID'],
    EntityType.Building: ['classID', 'mesh', 'shadowType', 'viewParamsIndex', 'cost', 'timeOfBuild', '$soundPackID', '$smokeID', '$killExplosionID', '$destructedID', 'hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'sightRange', '$talkPackID', '$shieldGeneratorID', 'maxShieldUpdate', 'slot1Type', 'slot2Type', 'slot3Type', 'slot4Type', 'buildingType', 'buildingTypeEx', 'buildingTabType', '$initCannonID1', '$initCannonID2', '$initCannonID3', '$initCannonID4', '$copulaID', 'buildingTunnelNumber', '$upgradeCopulaSmallID', '$upgradeCopulaBigID', '$buildLCTransporterID', '$chimneySmokeID', 'needPower', '$slaveBuildingID', 'maxSubBuildingsCount', 'powerLevel', 'powerTransmitterRange', 'connectTransmitterRange', 'fullEnergyPowerInDay', 'resourceInputOutput', 'ticPerContainer', '$containerID', 'containerSmeltingTicks', 'resourcesPerTransport', '$transporterID', '$buildingAmmoID', 'rangeOfBuildingFire', '$shootExplosionID', 'ammoReloadTime', '$buildExplosion', 'copulaAnimationFlags', 'endOfClosingCopulaAnimation', '$laserID', 'spaceStationType'],
    EntityType.Special: ['classID', 'mesh', 'shadowType', 'viewParamsIndex', 'cost', 'timeOfBuild', '$soundPackID', '$smokeID', '$killExplosionID', '$destructedID'],
    EntityType.Equipment: ['classID', 'mesh', 'shadowType', 'viewParamsIndex', 'cost', 'timeOfBuild', '$soundPackID', '$smokeID', '$killExplosionID', '$destructedID', 'rangeOfSight', 'plugType', 'slotType', 'maxAlphaPerTick', 'maxBetaPerTick'],
    EntityType.ShieldGenerator: ['shieldCost', 'shieldValue', 'reloadTime', 'shieldMeshName', 'shieldMeshViewIndex'],
    EntityType.SpecialUpdatesLinks: ['$specialUpdateLink']
}

class_field_map = {
    EntityClass.SUPPLYTRANSPORTER: ['ammoCapacity', 'animSupplyDownStart', 'animSupplyDownEnd', 'animSupplyUpStart', 'animSupplyUpEnd'],
    EntityClass.BUILDROBOT: ['$wallD', '$bridgeID', 'tunnelNumber', 'roadBuildTime', 'flatBuildTime', 'trenchBuildTime', 'tunnelBuildTime', 'buildObjectAnimationAngle', 'digNormalAnimationAngle', 'digLowAnimationAngle', 'animBuildObjectStartStart', 'animBuildObjectStartEnd', 'animBuildObjectWorkStart', 'animBuildObjectWorkEnd', 'animBuildObjectEndStart', 'animBuildObjectEndEnd', 'animDigNormalStartStart', 'animDigNormalStartEnd', 'animDigNormalWorkStart', 'animDigNormalWorkEnd', 'animDigNormalEndStart', 'animDigNormalEndEnd', 'animDigLowStartStart', 'animDigLowStartEnd', 'animDigLowWorkStart', 'animDigLowWorkEnd', 'animDigLowEndStart', 'animDigLowEndEnd', '$digSmokeID'],
    EntityClass.MININGROBOT: ['containersCnt', 'ticksPerContainer', 'putResourceAngle', 'animHarvestStartStart', 'animHarvestStartEnd', 'animHarvestWorkStart', 'animHarvestWorkEnd', 'animHarvestEndStart', 'animHarvestEndEnd', '$harvestSmokeID'],
    EntityClass.SAPPERROBOT: ['minesLookRange', '$mineID', 'maxMinesCount', 'animDownStart', 'animDownEnd', 'animUpStart', 'animUpEnd', '$putMineSmokeID'],
    EntityClass.PASSIVE: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'passiveMask', '$wallCopulaID'],
    EntityClass.MINE: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'mineSize', 'mineTypeOfDamage', 'mineDamage'],
    EntityClass.MULTIEXPLOSION: ['useDownBuilding', 'downBuildingStart', 'downBuildingTime', '$subObject1', 'time1', 'angle1', 'dist4X1', '$subObject2', 'time2', 'angle2', 'dist4X2', '$subObject3', 'time3', 'angle3', 'dist4X3', '$subObject4', 'time4', 'angle4', 'dist4X4', '$subObject5', 'time5', 'angle5', 'dist4X5', '$subObject6', 'time6', 'angle6', 'dist4X6', '$subObject7', 'time7', 'angle7', 'dist4X7', '$subObject8', 'time8', 'angle8', 'dist4X8'],
    EntityClass.BUILDPASSIVE: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'passiveMask', '$wallCopulaID'],
    EntityClass.PLATOON: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'sightRange', '$talkPackID', '$shieldGeneratorID', 'maxShieldUpdate', 'slot1Type', 'slot2Type', 'slot3Type', 'slot4Type'],
    EntityClass.TRANSIENTPASSIVE: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'passiveMask', '$wallCopulaID'],
    EntityClass.EXPLOSION: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'explosionTicks', 'explosionFlags'],
    EntityClass.EXPLOSIONEX: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'explosionTicks', 'explosionFlags'],
    EntityClass.FLYINGWASTE: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'wasteSize', '$subWasteID1', 'subWaste1Alpha', '$subWasteID2', 'subWaste2Alpha', '$subWasteID3', 'subWaste3Alpha', '$subWasteID4', 'subWaste4Alpha', 'flightTime', 'wasteSpeed', 'wasteDistanceX4', 'wasteBeta'],
    EntityClass.UPGRADECOPULA: ['rangeOfSight', 'plugType', 'slotType', 'maxAlphaPerTick', 'maxBetaPerTick'],
    EntityClass.STARTINGPOSITIONMARK: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'sightRange', '$talkPackID', '$shieldGeneratorID', 'maxShieldUpdate', 'slot1Type', 'slot2Type', 'slot3Type', 'slot4Type', 'positionType'],
    EntityClass.SMOKE: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'mesh1', 'mesh2', 'mesh3', 'smokeTime1', 'smokeTime2', 'smokeTime3', 'smokeFrequency', 'startingTime', 'smokingTime', 'endingTime', 'smokeUpSpeed', 'newSmokeDistance'],
    EntityClass.ARTEFACT: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'passiveMask', '$wallCopulaID', 'artefactMask', 'artefactParam', 'respawnTime'],
    EntityClass.BUILDINGTRANSPORTER: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'sightRange', '$talkPackID', '$shieldGeneratorID', 'maxShieldUpdate', 'slot1Type', 'slot2Type', 'slot3Type', 'slot4Type', 'vehicleSpeed', 'verticalVehicleAnimationType', '$builderLineID'],
    EntityClass.WALLLASER: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType'],
    EntityClass.RESOURCETRANSPORTER: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'sightRange', '$talkPackID', '$shieldGeneratorID', 'maxShieldUpdate', 'slot1Type', 'slot2Type', 'slot3Type', 'slot4Type', 'vehicleSpeed', 'verticalVehicleAnimationType', 'resourceVehicleType', 'animatedTransporterStop', 'showVideoPerTransportersCount', 'totalOrbitalMoney'],
    EntityClass.BUILDERLINE: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType'],
    EntityClass.UNITTRANSPORTER: ['hp', 'regenerationHP', 'armour', 'calorificCapacity', 'disableResist', 'storeableFlags', 'standType', 'sightRange', '$talkPackID', '$shieldGeneratorID', 'maxShieldUpdate', 'slot1Type', 'slot2Type', 'slot3Type', 'slot4Type', 'vehicleSpeed', 'verticalVehicleAnimationType', 'unitsCount', 'dockingHeight', 'animLoadingStartStart', 'animLoadingStartEnd', 'animLoadingEndStart', 'animLoadingEndEnd', 'animUnloadingStartStart', 'animUnloadingStartEnd', 'animUnloadingEndStart', 'animUnloadingEndEnd'],
    EntityClass.REPAIRER: ['repairerFlags', 'repairHPPerTick', 'repairElectronicsPerTick', 'ticksPerRepair', 'convertTankTime', 'convertBuildingTime', 'convertHealthyTankTime', 'convertHealthyBuildingTime', 'repaintTankTime', 'repaintBuildingTime', 'upgradeTankTime', 'animRepairStartStart', 'animRepairStartEnd', 'animRepairWorkStart', 'animRepairWorkEnd', 'animRepairEndStart', 'animRepairEndEnd', 'animConvertStartStart', 'animConvertStartEnd', 'animConvertWorkStart', 'animConvertWorkEnd', 'animConvertEndStart', 'animConvertEndEnd', 'animRepaintStartStart', 'animRepaintStartEnd', 'animRepaintWorkStart', 'animRepaintWorkEnd', 'animRepaintEndStart', 'animRepaintEndEnd'],
    EntityClass.CONTAINERTRANSPORTER: ['animContainerDownStart', 'animContainerDownEnd', 'animContainerUpStart', 'animContainerUpEnd'],
    EntityClass.LOOKROUNDEQUIPMENT: ['lookRoundTypeMask', 'lookRoundRange', 'turnSpeed', 'bannerAddExperienceLevel', 'regenerationHPMultiple', 'shieldReloadAdd'],
    EntityClass.TRANSPORTERHOOK: ['animTransporterDownStart', 'animTransporterDownEnd', 'animTransporterUpStart', 'animTransporterUpEnd', 'angleToGetPut', 'angleOfGetUnitByLandTransporter', 'takeHeight']
}


enum_mappings = {
    'classID': EntityClass
}


class Research:
    def __init__(self, stream):
        req_research_count = read_int(stream)
        self.previous = [read_int(stream) for _ in range(req_research_count)]
        self.id = read_int(stream)
        self.faction = Faction(read_int(stream))
        self.campaign_cost = read_int(stream)
        self.skirmish_cost = read_int(stream)
        self.campaign_time = read_int(stream)
        self.skirmish_time = read_int(stream)
        self.name = read_string(stream)
        self.video = read_string(stream)
        self.type = ResearchTab(read_int(stream))
        self.mesh = read_string(stream)
        self.meshParamsIndex = read_int(stream)

    def __repr__(self):
        items = ("%s=%r" % (k, v) for k, v in self.__dict__.items())
        return "%s{%s}" % (self.__class__.__name__, ', '.join(items))


class Entity:
    def __init__(self, stream):
        self.name = read_string(stream)
        req_research_count = read_int(stream)
        self.req_research = [read_int(stream) for _ in range(req_research_count)]
        field_count = read_int(stream)
        field_types = stream.read(field_count)
        self.fields = list()
        for (i, is_string) in enumerate(field_types):
            if is_string:
                self.fields.append(read_string(stream))
            else:
                val = read_int(stream)
                # Skip the -1 after every string
                if not (val == 0xffffffff and i > 0 and field_types[i-1]):
                    self.fields.append(val)

    def __repr__(self):
        return f'Entity{{name={self.name!r}, req_research={self.req_research}, fields={len(self.fields)}{self.fields}}}'


class EntityGroup:
    def __init__(self, stream):
        self.faction = Faction(read_int(parfile))
        self.entity_type = EntityType(read_int(parfile))
        entity_count = read_int(parfile)
        self.entities = [Entity(stream) for _ in range(entity_count)]

    def __repr__(self):
        entities = ''
        for entity in self.entities:
            entities += f'  {entity}\n'
        return f'EntityGroup{{faction={self.faction}, entity_type={self.entity_type}, entities=\n{entities}}}'


class CsvFileManager:
    def __init__(self, directory=os.curdir):
        self.directory = directory
        self.files = dict()
        self.writers = dict()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        for f in self.files.values():
            f.close()

    def get(self, entity_group):
        class_id = None
        fields = None
        if entity_group.entity_type in [EntityType.Vehicle, EntityType.Cannon, EntityType.Missile, EntityType.Building, EntityType.Special, EntityType.Equipment]:
            try:
                class_id = EntityClass(entity_group.entities[0].fields[0])
                if class_id == EntityClass.EXPLOSIONEX:
                    class_id = EntityClass.EXPLOSION
                elif class_id in [EntityClass.BUILDPASSIVE, EntityClass.TRANSIENTPASSIVE]:
                    class_id = EntityClass.PASSIVE
                name = EntityClass(class_id).name.lower()
            except ValueError:
                print(f'{class_id:08x}', entity_group)
                raise
        elif entity_group.entity_type == EntityType.SoundPack:
            first_name = entity_group.entities[0].name
            if first_name.startswith('TALK_'):
                name = 'talkpack'
                fields = ['selected', 'move', 'attack', 'command', 'enemy', 'help', 'freeWay']
            elif first_name.startswith('PLAYERTALK_'):
                name = 'playertalkpack'
                fields = ['baseUnderAttack', 'buildingUnderAttack', 'spacePortUnderAttack', 'enemyLandInBase', 'lowMaterials', 'lowMaterialsInBase', 'lowPower', 'lowPowerInBase', 'researchComplete', 'productionStarted', 'productionCompleted', 'productionCanceled', 'platoonLost', 'platoonCreated', 'platoonDisbanded', 'unitLost', 'transporterArrived', 'artefactLocated', 'artefactRecovered', 'newAreaLocationFound', 'enemyMainBaseLocated', 'newSourceFieldLocated', 'sourceFieldExploited', 'buildingLost']
            else:
                name = 'soundpack'
                fields = ['normalWavePack1', 'normalWavePack2', 'normalWavePack3', 'normalWavePack4', 'loopedWavePack1', 'loopedWavePack2', 'loopedWavePack3', 'loopedWavePack4']
        elif entity_group.entity_type == EntityType.Parameters:
            fields = []
            name = 'parameters'
        else:
            name = entity_group.entity_type.name.lower()

        if name not in self.writers:
            path = os.path.relpath(name + '.csv', self.directory)
            self.files[name] = open(path, 'w', newline='')
            self.writers[name] = csv.writer(self.files[name], lineterminator='\n')
            if fields is None:
                fields = ['name', 'research'] + type_field_map.get(entity_group.entity_type, []) + class_field_map.get(class_id, [])
            self.writers[name].writerow(fields) # header
        return self.writers[name]

    def __repr__(self):
        return f'FileManager{{directory={self.directory!r}, files={list(self.files.keys())}}}'


def resnames(research, ids):
    return ' '.join(research[id].name for id in ids)

try:
    with open(filename, 'rb') as parfile:
        headers = parfile.read(16)
        entity_group_count = int.from_bytes(headers[8:12], byteorder='little')

        entity_groups = [EntityGroup(parfile) for _ in range(entity_group_count)]

        research_count = read_int(parfile)
        research = [Research(parfile) for _ in range(research_count)]
        research_ids = {r.id : r for r in research}
except FileNotFoundError:
    print(usage)
    sys.exit(1)

with open('research.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, ['name', 'faction', 'campaign_cost', 'skirmish_cost', 'campaign_time', 'skirmish_time', 'video', 'type', 'mesh', 'meshParamsIndex', 'previous'], lineterminator='\n')
    writer.writeheader()
    for r in sorted(research, key=lambda r: r.id):
        r = vars(r)
        del(r['id'])
        r['previous'] = resnames(research, r['previous'])
        writer.writerow(r)
    print('Wrote research to research.csv')

with CsvFileManager() as fm:
    for (i, group) in enumerate(entity_groups):
        writer = fm.get(group)
        writer.writerow([f'Group {i}', group.faction.name])
        for e in group.entities:
            writer.writerow([e.name, resnames(research, e.req_research)] + e.fields)
        writer.writerow([])
    print(f"Wrote entities to {', '.join(name + '.csv' for name in fm.files.keys())}.")

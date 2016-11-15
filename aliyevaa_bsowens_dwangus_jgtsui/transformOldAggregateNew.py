import json
import dml
import prov.model
import datetime
import uuid
import time
import ast
from geopy.distance import vincenty as vct
from bson.code import Code

class transformOldAggregateNew(dml.Algorithm):
    contributor = 'aliyevaa_bsowens_dwangus_jgtsui'

    oldSetExtensions = ['crime2012_2015', 'public_fishing_access_locations', 'moving_truck_permits', \
                     'food_licenses', 'entertainment_licenses', 'csa_pickups', 'year_round_pools']

    
    oldTitles = ['Crime Incident Reports (July 2012 - August 2015) (Source: Legacy System)', \
              'Public Access Fishing Locations', 'Issued Moving Truck Permits', 'Active Food Establishment Licenses', \
              'Entertainment Licenses', 'Community Supported Agriculture (CSA) Pickups ', 'Year-Round Swimming Pools']
    titles = ['Crime in 1-Mile Radius of Community Indicators', \
              'Crime in 1-Mile Radius of Anti-Community Indicators', \
              'Crime in 1-Mile Radius of Moving Truck Permits']
    setExtensions = ['crimeVanti_community_indicators', 'crimeVcommunity_indicators']

    reads = ['aliyevaa_bsowens_dwangus_jgtsui.' + dataSet for dataSet in oldSetExtensions]
    writes = ['aliyevaa_bsowens_dwangus_jgtsui.' + dataSet for dataSet in oldSetExtensions]

    dataSetDict = {}
    for i in range(len(oldSetExtensions)):
        dataSetDict[oldSetExtensions[i]] = (writes[i], oldTitles[i])
    print(dataSetDict)

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets.'''
        startTime = datetime.datetime.now()
        print("Starting execution of script @{}".format(startTime))
        start = time.time()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate(transformOldAggregateNew.contributor, transformOldAggregateNew.contributor)
        myrepo = repo.aliyevaa_bsowens_dwangus_jgtsui



        for key in transformOldAggregateNew.oldSetExtensions:
            print(key)
            print(myrepo[key].find_one())
            print("\n")

        #Wow, that's really interesting... no crimes occurred where, in the vicinity of 1 mile, there were 23 "community centers" nearby
        #In contrast, no crimes only began to stop occurring where, in the same radius, there were 2918 "entertainment/food" licensees nearby
        #And no crimes happen where, in the same radius of 1 mile, there were 557 moving truck permits issued
        #...Hmm... I didn't cross-reference these with time though...

        print(myrepo['crimeVcommunity_indicators'].find({'community_indicators_1600m_radius': {'$gt': 23}}).count())
        print(myrepo['crimeVanti_community_indicators'].find({'anti_community_indicators_1600m_radius': {'$gt': 2917}}).count())

        #return
        '''
        #'''
        indicatorsColl = myrepo['community_indicators']
        repo.createPermanent('community_indicators')
        anti_indicatorsColl = myrepo['anti_community_indicators']
        repo.createPermanent('anti_community_indicators')


        print(transformOldAggregateNew.dataSetDict.keys())
        for key in transformOldAggregateNew.dataSetDict.keys():
            begin = time.time()
            
            repo.drop_collection(key)


        ##print(myrepo['crimeVcommunity_indicators'].find({'community_indicators_1600m_radius': {'$gt': 23}}).count())
        ##print(myrepo['crimeVanti_community_indicators'].find({'anti_community_indicators_1600m_radius': {'$gt': 2917}}).count())
        ##print(myrepo['crimeVmoving_truck_permits'].find({'moving_indicators_1600m_radius': {'$gt': 557}}).count())
        ##return

        for key in transformOldAggregateNew.dataSetDict.keys():
            begin = time.time()

            repo.dropPermanent(key)
            repo.createPermanent(key)

            print("Now copying {} entries from crime2012_2015 to create new dataset {}.\n".format(myrepo['crime2012_2015'].count(), key))
            #"Now copying 268056 entries from crime2012_2015 to create new dataset crimeVcommunity_indicators."

            #myrepo[key].insert_many(myrepo['crime2012_2015'].find())
            #Or:
            #repo[transformOldAggregateNew.dataSetDict[key][0]].insert(myrepo['crime2012_2015'].find())

            newSet = myrepo[key]
            newSet.create_index([('location', '2dsphere')])
            indicatorsColl.create_index([('location', '2dsphere')])
            anti_indicatorsColl.create_index([('location', '2dsphere')])


            communityIndicators = ['public_fishing_access_locations','csa_pickups','year_round_pools']
            anti_communityIndicators = ['food_licenses', 'entertainment_licenses','parking']
            print("Generating new {} dataset...".format(key))
            if key in communityIndicators:
                #"Creating crimeVcommunity_indicators took 512.1758079528809 seconds."
                i = 0
                for doc in newSet.find(modifiers={"$snapshot": True}):
                    if (i%100 == 0):
                        print(i)
                    i += 1
                    if 'location' in doc.keys():

                        #get the title of the business, based on common title keys

                        if key == 'public_fishing_access_locations':
                            title = doc['name']
                        elif key == 'csa_pickups':
                            title = doc['name']
                        elif key == 'year_round_pools':
                            title = doc['business_name']
                        else: title = "unknownName " + i

                        indicatorsColl.insert({'title': title, 'type':key,
                                             'location': doc['location'],
                                            'community_score': 1})

            elif key in anti_communityIndicators:
                #Creating crimeVanti_community_indicators took 2504.4606323242188 seconds.
                # "Creating crimeVcommunity_indicators took 512.1758079528809 seconds."
                i = 0
                for doc in newSet.find(modifiers={"$snapshot": True}):
                    if (i % 100 == 0):
                        print(i)
                    i += 1
                    if 'location' in doc.keys():
                        # get the title of the business, based on common title keys
                        if key == 'entertainment_licenses':
                            title = doc['dbaname']
                        elif key == 'food_licenses':
                            title = doc['businessname']
                        elif key == 'parking':
                            title = doc['name']
                        else: title = 'unknownName ' + i


                        indicatorsColl.insert({'id': doc['_id'], 'title': title, 'type': key,
                                                    'location': doc['location'],
                                               'community_score': -1})
            '''
            else:
                #"Creating crimeVmoving_truck_permits took 658.3249619007111 seconds."
                #i = 0
                for doc in newSet.find(modifiers={"$snapshot": True}):
                    #if (i%1000 == 0):
                    #    print(i)
                    if 'location' in doc.keys():
                        newSet.update({'_id': doc['_id']}, \
                                      {'$set': \
                                       {'moving_indicators_1600m_radius': \
                                        myrepo['moving_truck_permits'].find({'location': {'$near': {'$geometry': doc['location'], '$maxDistance': 1600}}}).count()\
                                        }\
                                       }\
                                      )
                    #i += 1
            #'''
            print("Creating {} took {} seconds.".format(key, time.time() - begin))

        repo.logout()

        endTime = datetime.datetime.now()
        print("\nTransformation/manipulation of old + storage of new datasets took:\n{} seconds\n...and ended at:\n{}\n".format(time.time() - start, endTime))
        #"Transformation/manipulation of old + storage of new datasets took:
        #3675.0184156894684 seconds
        #...and ended at:
        #2016-10-07 06:58:25.821880"
        return {"start":startTime, "end":endTime}

    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
        Create the provenance document describing everything happening
        in this script. Each run of the script will generate a new
        document describing that invocation event.
        '''

         # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate(transformOldAggregateNew.contributor, transformOldAggregateNew.contributor)

        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:aliyevaa_bsowens_dwangus_jgtsui#transformOldAggregateNew', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        for key in transformOldAggregateNew.dataSetDict.keys():
            #How to say that this dataset was generated from multiple sources?
            #resource = doc.entity('dat:' + transformOldAggregateNew.contributor + '#' + key???, {'prov:label':transformOldAggregateNew.dataSetDict[key][1], prov.model.PROV_TYPE:'ont:DataSet'})
            get_something = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
            doc.wasAssociatedWith(get_something, this_script)
            something = doc.entity('dat:aliyevaa_bsowens_dwangus_jgtsui#' + key, {prov.model.PROV_LABEL:transformOldAggregateNew.dataSetDict[key][1], prov.model.PROV_TYPE:'ont:DataSet'})
            doc.wasAttributedTo(something, this_script)
            doc.wasGeneratedBy(something, get_something, endTime)
            #doc.wasDerivedFrom(something, resource???, get_something, get_something, get_something)


        '''
        doc.usage(get_found, resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?type=Animal+Found&$select=type,latitude,longitude,OPEN_DT'
                }
            )
        doc.usage(get_lost, resource, startTime, None,
                {prov.model.PROV_TYPE:'ont:Retrieval',
                 'ont:Query':'?type=Animal+Lost&$select=type,latitude,longitude,OPEN_DT'
                }
            )
        #'''


        repo.record(doc.serialize()) # Record the provenance document.
        repo.logout()

        return doc

transformOldAggregateNew.execute()
#doc = transformOldAggregateNew.provenance()
#print(doc.get_provn())
#print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof

function waitForNode(host) {
    while (true) {
        try {
            let db = new Mongo(host).getDB("admin");
            if (db.runCommand({ ping: 1 }).ok === 1) {
                print("Node " + host + " is ready.");
                break;
            }
        } catch (e) {
            print("Waiting for " + host + "...");
            sleep(2000);
        }
    }
}

waitForNode("mongo-cfg:27017");
waitForNode("mongo-shard1:27017");
waitForNode("mongo-shard2:27017");
waitForNode("mongo-shard3:27017");

const cfgAdmin = new Mongo("mongo-cfg:27017").getDB("admin");
cfgAdmin.runCommand({
    replSetInitiate: {
        _id: "cfgRS",
        configsvr: true, 
        members: [{_id: 0, host: "mongo-cfg:27017"}]
    }
});

const shard1Admin = new Mongo("mongo-shard1:27017").getDB("admin");
shard1Admin.runCommand({
  replSetInitiate: {
    _id: "shard1RS",
    members: [{_id: 0, host: "mongo-shard1:27017"}]
  }
});

const shard2Admin = new Mongo("mongo-shard2:27017").getDB("admin");
shard2Admin.runCommand({
    replSetInitiate:{
        _id: "shard2RS",
        members: [{_id: 0, host: "mongo-shard2:27017"}]
    }
});

const shard3Admin = new Mongo("mongo-shard3:27017").getDB("admin");
shard3Admin.runCommand({
    replSetInitiate:{
        _id: "shard3RS",
        members: [{_id: 0, host: "mongo-shard3:27017"}]
    }
});


waitForNode("mongos:27017");
sleep(5000);

const mongosAdmin = new Mongo("mongos:27017").getDB("admin");
mongosAdmin.runCommand({ addShard: "shard1RS/mongo-shard1:27017" });
mongosAdmin.runCommand({ addShard: "shard2RS/mongo-shard2:27017" });
mongosAdmin.runCommand({ addShard: "shard3RS/mongo-shard3:27017" });

mongosAdmin.runCommand({ enableSharding: "recipes" });
mongosAdmin.runCommand({ 
    shardCollection: "recipes.recipes", 
    key: { _id: "hashed" } 
});
const recipesDB = new Mongo("mongos:27017").getDB("recipes");
recipesDB.recipes.createIndex({ cuisine: 1, cook_time_min: 1, calories: 1 });
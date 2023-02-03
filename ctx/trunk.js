import fs from 'fs'
import brain from 'brain.js'
import Gun from 'gun'
import SEA from 'gun/sea.js'
import 'gun/lib/radix.js'
import 'gun/lib/radisk.js'
import 'gun/lib/store.js'
import 'gun/lib/rindexed.js'
import 'gun/lib/webrtc.js'
import express from 'express'

let port = process.env.PORT || 9666
let payload = ''

// Start a web server
const app = express()

// Publish the brain at the root
app.get('/', (req, res) => {
  res.send(payload)
})

// Expose the brain stem to a local API
const server = app.listen(port, () => {
  console.log(`The stem is exposed on port: ${port}`)
})

// Connect to the hivemind
const gun = Gun({
  peers: ['http://ctx:9666/gun', 'https://59.thesource.fm/gun'],
  web: server,
  file: './hive',
  localStorage: false,
  radisk: true,
  axe: true
})

// Generate credentials
let user = null
const identity = randomString(randomBetween(96, 128))
const identifier = randomString(64)

// Authenticate with the cockpit
async function cockpit(identity, identifier) {
  console.log('identity :> ' + identity)
  console.log('identifier :> ' + identifier)
  console.log('loading coke pit')
  await authenticateUser(identity, identifier)
}

cockpit(identity, identifier)

// Capture every message published at this channel
let bullet
const channel = gun
  .get('messaging')
  .get('channels')
  .get('support')
  .on(async (node) => {
    try {
      if (typeof node.payload === 'string') {
        bullet = node.payload
      }
    } catch {}
  })

// Publish every message at this route
app.get('/channel', (req, res) => {
  res.json(bullet)
})

// Receive messages from vtx at this route
app.use(express.json())
app.post('/message', async (req, res) => {
  console.log('pang')
  try {
    // Destructure and sign message
    let { message, identifier, pubKey } = req.body
    if (user) {
      message = await SEA.sign(message, pair)
      pubKey = pair.pub
    }
    // Send message to GUN
    const payload = JSON.stringify({ identifier, message, pubKey })
    await channel.get('payload').put(payload)
  } catch (err) {
    console.error(err)
    console.error('failed to send a message')
    console.log('trying to connect once again')
    cockpit(identity, identifier)
  }
  res.json('ok')
})

// Ingest a seed
const seed = JSON.parse(fs.readFileSync('ctx/seed.json', 'utf-8'))

// Instantiate the brain
const net = new brain.recurrent.LSTM({
  hiddenLayers: [9],
  inputSize: 2,
  maxPredictionLength: 2,
  outputSize: 1
})

// Train the model on the seed
net.train(seed, {
  errorThresh: 0.1,
  iterations: 10000,
  // timeout: Infinity,
  learningRate: 0.3,
  log: (details) => console.log(details),
  logPeriod: 2000
})

// Publish brain updates to GUN
const state = gun
  .get('brain')
  .get('state')
  .on(async (node) => {
    if (typeof node.payload === 'string') {
      try {
        net.fromJSON(JSON.parse(node.payload))
        payload = node.payload
      } catch {
        console.log('failed to load brain from json')
      }
    }
  })

// Place brain in GUN at startup
state.get('payload').put(JSON.stringify(net.toJSON()))

// LSTM prediction step
console.log(`PEN@FOLD: ` + 'i predict ' + net.run(['.', '..']))

// Generate a cryptographically-secure random string
function randomString(length) {
  let result = ''
  const characters = 'abcdef0123456789'
  const charactersLength = characters.length
  let counter = 0
  while (counter < length) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength))
    counter += 1
  }
  return result
}

// Get a random number between two others
export function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min) + min)
}

// Create a GUN user
let pair = null
async function authenticateUser(identity, identifier) {
  try {
    user = gun.user()
    user.auth(identifier, identity, async (data) => {
      if (data.err) {
        user.create(identifier, identity, async (data) => {
          console.log('Creating GUN user: ~' + data.pub)
          authenticateUser(identity, identifier)
        })
      } else {
        pair = user.pair()
        console.log('Authenticated GUN user: ~' + pair.pub)
      }
    })
  } catch (err) {
    console.error(err)
  }
}

// Delay by x number of milliseconds
const delay = (ms) => new Promise((res) => setTimeout(res, ms))

const randomValueFromArray = (array) => {
  return array[Math.floor(Math.random() * array.length)]
}

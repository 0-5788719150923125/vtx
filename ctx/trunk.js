import fs from 'fs'
import http from 'http'
import crypto from 'crypto'
import brain from 'brain.js'
import Gun from 'gun'
import SEA from 'gun/sea.js'
import 'gun/lib/radix.js'
import 'gun/lib/radisk.js'
import 'gun/lib/store.js'
import 'gun/lib/rindexed.js'
import 'gun/lib/webrtc.js'
// import { create } from 'ipfs-http-client'
import express from 'express'

let port = process.env.PORT || 9666
let payload = ''

const delay = (ms) => new Promise((res) => setTimeout(res, ms))

const app = express()

app.get('/', (req, res) => {
  res.send(payload)
})

const server = app.listen(port, () => {
  console.log(`The Root is exposed on port: ${port}`)
})

// Connect to the hivemind
const gun = Gun({
  peers: ['http://ctx:9665/gun', 'https://59.thesource.fm/gun'],
  web: server,
  file: './gun',
  localStorage: false,
  radisk: true,
  axe: true
})

// Generate credentials
const identity = randomString(randomBetween(96, 128))
const identifier = randomString(64)

let user = null
async function cockpit(identity, identifier) {
  console.log(identity)
  console.log(identifier)
  console.log('loading coke pit')
  await authenticateUser(identity, identifier)
}

cockpit(identity, identifier)

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

app.get('/channel', (req, res) => {
  res.json(bullet)
})

app.use(express.json())
app.post('/message', async (req, res) => {
  try {
    const { message, identifier, pubKey } = req.body
    if (user) {
      message = await SEA.sign(message, pair)
      pubKey = pair.pub
    }
    // if (opts.password !== false) message = encrypt(message, opts.password)
    const payload = JSON.stringify({ identifier, message, pubKey })
    // messageCache.push(payload)
    await channel.get('payload').put(payload)
    channel.get('payload').put(JSON.stringify({ message, identifier, pubKey }))
    res.json('ok')
  } catch {
    console.error('failed to send a message')
    res.json('ok')
  }
})

const seed = JSON.parse(fs.readFileSync('ctx/seed.json', 'utf-8'))

const net = new brain.recurrent.LSTM({
  hiddenLayers: [9],
  inputSize: 2,
  maxPredictionLength: 2,
  outputSize: 1
})

// const randomValueFromArray = (array) => {
//   return array[Math.floor(Math.random() * array.length)]
// }

net.train(seed, {
  errorThresh: 0.1,
  iterations: 10000,
  // timeout: Infinity,
  learningRate: 0.3,
  log: (details) => console.log(details),
  logPeriod: 2000
})

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

state.get('payload').put(JSON.stringify(net.toJSON()))

console.log('i predict ' + net.run(['.', '..']))

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
        let pair = user.pair()
        console.log('Authenticated GUN user: ~' + pair.pub)
      }
    })
  } catch (err) {
    console.error(err)
  }
}

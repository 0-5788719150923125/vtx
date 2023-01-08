import fs from 'fs'
import http from 'http'
import crypto from 'crypto'
import brain from 'brain.js'
import Gun from 'gun'
import SEA from 'gun/sea.js'
// import { create } from 'ipfs-http-client'

// async function testIPFS() {
//   const ipfs = create({ url: '/ip4/127.0.0.1/tcp/5001' })
//   const { cid } = await ipfs.add('Hello world!')
//   console.log(cid)
//   const id = await ipfs.id()
//   const addresses = await ipfs.swarm.localAddrs()
//   // console.log(addresses)
//   console.log(id)
// }

// testIPFS()

let payload = ''
let port = process.env.PORT || 9666

const delay = (ms) => new Promise((res) => setTimeout(res, ms))
const requestListener = function (req, res) {
  res.writeHead(200)
  res.end(payload)
}

const server = http.createServer(requestListener).listen(port, function () {
  console.log(`server listening on port: ${port}`)
})

const gun = Gun({
  peers: [
    'https://59.thesource.fm/gun',
    'http://vtx:9666/gun',
    'http://localhost:9666/gun',
    'http://localhost:9665/gun'
  ],
  web: server,
  file: './vtx/lab',
  localStorage: false,
  radisk: true,
  axe: true
})

const seed = JSON.parse(fs.readFileSync('./seed.json', 'utf-8'))

console.warn('my seed')
console.log(seed)

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

const channel = gun
  .get('messaging')
  .get('channels')
  .get('support')
  .on(async (node) => {
    if (typeof node.payload === 'string') {
      state.get('payload').put(JSON.stringify(net.toJSON()))
    }
  })

state.get('payload').put(JSON.stringify(net.toJSON()))

console.log('i predict ' + net.run(['.', '..']))

// const fire = async () => {
//   let bullet
//   if (crypto.randomInt(0, 2) === 1) {
//     bullet = {
//       identifier: 23,
//       consensus: '.:'
//     }
//   } else {
//     bullet = {
//       identifier: 24,
//       consensus: ':.'
//     }
//   }
//   channel.get('payload').put(JSON.stringify(bullet))
//   await delay(8888)
//   fire()
// }

// fire()
// for (let i = 0; i < cpuCount.cpus().length; i++) {
//     console.log(`Forking process number ${i}...`)

//     cluster.fork() //creates new node js processes
// }

import fs from 'fs'
import http from 'http'
import crypto from 'crypto'
import brain from 'brain.js'
import Gun from 'gun'
import SEA from 'gun/sea.js'

let payload = ''
const port = process.env.PORT || 9666

const requestListener = function (req, res) {
  res.writeHead(200)
  res.end(JSON.stringify(payload))
}

const server = http.createServer(requestListener).listen(port, function () {
  console.log(`server listening on port: ${port}`)
})

const gun = Gun({
  peers: ['https://59.thesource.fm/gun', 'http://vtx:9666/gun'],
  web: server,
  file: './vtx/lab',
  localStorage: false,
  radisk: true,
  axe: true
})

const channel = gun
  .get('messaging')
  .get('channels')
  .get('support')
  .on(async (node) => {
    if (typeof node.payload === 'string') {
      payload = JSON.parse(node.payload)
      console.log(payload.consensus)
    }
  })

const delay = (ms) => new Promise((res) => setTimeout(res, ms))
const fire = async () => {
  let bullet
  if (crypto.randomInt(0, 2) === 1) {
    bullet = {
      identifier: 23,
      consensus: '.:'
    }
  } else {
    bullet = {
      identifier: 24,
      consensus: ':.'
    }
  }
  channel.get('payload').put(JSON.stringify(bullet))
  await delay(8888)
  fire()
}

fire()

const seed = JSON.parse(fs.readFileSync('./seed.json', 'utf-8'))
const net = new brain.recurrent.LSTM({
  hiddenLayers: [9, 8, 6, 3],
  inputSize: 2,
  // maxPredictionLength: 7,
  outputSize: 1
})

console.warn('my seed')
console.log(seed)

const randomValueFromArray = (array) => {
  return array[Math.floor(Math.random() * array.length)]
}

let choice
net.train(seed, {
  errorThresh: 0.1,
  iterations: Infinity,
  timeout: Infinity,
  learningRate: 0.1,
  log: (details) => console.log(details),
  logPeriod: 6666,
  // callback: net.run(randomValueFromArray(seed)),
  callback: () => {
    fs.writeFileSync('./brain.json', JSON.stringify(net.toJSON()))
    console.log('state = ' + JSON.stringify(randomValueFromArray(seed)))
    choice = randomValueFromArray(seed)
    console.log(choice)
  },
  callbackPeriod: 6667
})

// console.log(choice)
// net.run({ input: ['.', '..'] })

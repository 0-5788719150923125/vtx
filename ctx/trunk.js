import fs from 'fs'
import brain from 'brain.js'
import Gun from 'gun'
import SEA from 'gun/sea.js'
import 'gun/lib/radix.js'
import 'gun/lib/radisk.js'
import 'gun/lib/store.js'
import 'gun/lib/rindexed.js'
import 'gun/lib/webrtc.js'
import 'gun/lib/open.js'
import 'gun/lib/load.js'
import express from 'express'
import yaml from 'js-yaml'

let config = null
const defaultConfig = yaml.load(fs.readFileSync('/vtx/vtx/default.yml', 'utf8'))

// Merge user config with default config
try {
  const userConfig = yaml.load(fs.readFileSync('/vtx/lab/config.yml', 'utf8'))
  config = {
    ...defaultConfig.source,
    ...userConfig.source
  }
} catch {
  config = {
    ...defaultConfig.source
  }
}

console.log(config)

let port = process.env.PORT || 9666
let payload = ''

const bc = {
  ROOT: '\x1b[32m',
  CORE: '\x1b[31m',
  FOLD: '\x1b[34m'
}

const ad = {
  TEXT: '\x1b[37m'
}

// Delay by x number of milliseconds
const delay = (ms) => new Promise((res) => setTimeout(res, ms))

// Get a random number between two others
function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min) + min)
}

// Get a random value from an array
const randomValueFromArray = (array) => {
  return array[Math.floor(Math.random() * array.length)]
}

// Start a web server
const app = express()

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

// Authenticate with GUN
async function cockpit(identity, identifier) {
  console.log('identity :> [REDACTED]')
  console.log('identifier :> ' + identifier)
  console.log('loading into cockpit')
  await authenticateUser(identity, identifier)
}

cockpit(identity, identifier)

// All following routes will use JSON
app.use(express.json())

// Capture every message published at every configured channel
const channels = {}
for (const channel of Object.entries(config)) {
  channels[channel] = channel
  channel['gun'] = gun
    .get('messaging')
    .get('channels')
    .get(channel[0])
    .on(async (node) => {
      try {
        if (typeof node.payload === 'string') {
          const payload = JSON.parse(node.payload)
          let message = 'ERROR: Me Found.'
          if (
            payload.pubKey !== null &&
            typeof payload.pubKey !== 'undefined'
          ) {
            const sender = await gun.user(`${payload.pubKey}`)
            message = await SEA.verify(payload.message, sender.pub)
          } else {
            message = payload.message
          }
          channel['bullet'] = {
            message,
            identifier: payload.identifier
          }
        }
      } catch (err) {
        console.error(err)
      }
    })
  // Publish messages at these routes
  app.get(`/channel/${channel[0]}`, (req, res) => {
    res.json(channel['bullet'])
  })

  // Receive messages from vtx at these routes
  app.post(`/message/${channel[0]}`, async (req, res) => {
    try {
      // Destructure and sign message
      let { message, identifier } = req.body
      let pubKey = null
      if (user) {
        message = await SEA.sign(message, pair)
        pubKey = pair.pub
      }
      // Send message to GUN
      const payload = JSON.stringify({ identifier, message, pubKey })
      await channel['gun'].get('payload').put(payload)
      console.log(bc.ROOT + 'ONE@ROOT: ' + ad.TEXT + 'pang')
    } catch (err) {
      console.error(err)
      cockpit(identity, identifier)
    }
    res.json('ok')
  })
}

// Hash strings into daemon names at this route
app.get('/daemon', (req, res) => {
  if (typeof req.body.seed === 'undefined') return res.json('missing payload')
  const daemon = ng.generateOne(req.body.seed.toString())
  res.json({ name: daemon })
})

// Ingest a seed
const seed = JSON.parse(fs.readFileSync('ctx/seed.json', 'utf-8'))

// Instantiate the brain
const net = new brain.recurrent.LSTM({
  hiddenLayers: [4],
  inputSize: 5,
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

function convertBrainToObject(obj) {
  if (Array.isArray(obj)) {
    const newObj = {}
    obj.forEach((element, index) => {
      newObj[index] = convertBrainToObject(element)
    })
    return newObj
  } else if (typeof obj === 'object' && obj !== null) {
    const newObj = {}
    for (let key in obj) {
      newObj[key] = convertBrainToObject(obj[key])
    }
    return newObj
  } else {
    return obj
  }
}

function restoreBrainFromObject(obj) {
  if (typeof obj === 'object' && obj !== null) {
    if (Object.keys(obj).every((key, i) => key == i && obj[key] !== null)) {
      const arr = []
      for (let key in obj) {
        arr[key] = restoreBrainFromObject(obj[key])
      }
      return arr
    } else {
      const newObj = {}
      for (let key in obj) {
        newObj[key] = restoreBrainFromObject(obj[key])
      }
      return newObj
    }
  } else {
    return obj
  }
}

// Publish the brain at the root
app.get('/', (req, res) => {
  net.fromJSON(JSON.parse(JSON.stringify(payload)))
  res.json(payload)
})

// Publish brain updates to GUN
const state = gun
  .get('state')
  .get('brain')
  .on(async (node) => {
    try {
      state.open((node) => {
        const restored = restoreBrainFromObject(node)
        payload = restored
      })
    } catch (err) {
      // pass
    }
  })

const nn = convertBrainToObject(net.toJSON())

const nnObject = JSON.parse(JSON.stringify(nn))

// Place brain in GUN at startup
state.put(nnObject)

// LSTM prediction step
console.log(
  bc.FOLD + `PEN@FOLD: ` + ad.TEXT + 'i predict ' + net.run(['.', '..'])
)

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

// Create a GUN user
let pair = null
async function authenticateUser(identity, identifier) {
  try {
    await delay(3000)
    user = gun.user()
    user.auth(identifier, identity, async (data) => {
      if (data.err) {
        user.create(identifier, identity, async (data) => {
          console.log('Creating GUN user: ~' + data.pub)
          await authenticateUser(identity, identifier)
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

const seededPRNG = (str) => {
  function xmur3(str) {
    for (var i = 0, h = 1779033703 ^ str.length; i < str.length; i++) {
      h = Math.imul(h ^ str.charCodeAt(i), 3432918353)
      h = (h << 13) | (h >>> 19)
    }
    return function () {
      h = Math.imul(h ^ (h >>> 16), 2246822507)
      h = Math.imul(h ^ (h >>> 13), 3266489909)
      return (h ^= h >>> 16) >>> 0
    }
  }
  function xoshiro128ss(a, b, c, d) {
    return function () {
      var t = b << 9,
        r = a * 5
      r = ((r << 7) | (r >>> 25)) * 9
      c ^= a
      d ^= b
      b ^= c
      a ^= d
      c ^= t
      d = (d << 11) | (d >>> 21)
      return (r >>> 0) / 4294967296
    }
  }
  const state = xmur3(str)
  const rand = xoshiro128ss(state(), state(), state(), state())
  return rand()
}

const NameGenerator = {
  initialize: function (corpus) {
    this.transitions = [[]]
    this.corpus = []
    corpus.forEach(
      function (string) {
        this.integrateString(string)
      }.bind(this)
    )
    return this
  },
  selectOne: function (a, seed) {
    return a[Math.floor(seed * a.length)]
  },
  forEachCharacter: function (s, f) {
    Array.prototype.forEach.call(s, f)
  },
  addTableElement: function (table, lastLetter, currentLetter) {
    const array = table[lastLetter] || []
    array.push(currentLetter)
    table[lastLetter] = array
  },
  integrateString: function (string) {
    let strLen = string.length,
      initial = this.transitions[0],
      lastLetter = string[0],
      currentLetter,
      currentTable,
      i
    if (strLen > 0) {
      initial.push(string[0])
      this.forEachCharacter(
        string.substring(1),
        function (currentLetter, index) {
          this.addTableElement(
            this.getNthTable(index + 1),
            lastLetter,
            currentLetter
          )
          lastLetter = currentLetter
        }.bind(this)
      )
      this.addTableElement(this.getNthTable(strLen), lastLetter, 'end')
      this.corpus.push(string)
    }
    return this
  },
  getNthTable: function (n) {
    const table = this.transitions[n] || {}
    this.transitions[n] = table
    return table
  },
  generateOne: function (seedString) {
    let seed = seededPRNG(seedString)
    let name = [this.selectOne(this.transitions[0], seed)],
      lastLetter = name[0],
      done = false,
      i = 1,
      currentLetter
    while (!done) {
      seed = seededPRNG(seedString + 'a')
      currentLetter = this.selectOne(this.getNthTable(i)[lastLetter], seed)
      if (currentLetter === 'end') {
        done = true
      } else {
        name.push(currentLetter)
        lastLetter = currentLetter
        i = i + 1
      }
    }
    return name.join('')
  }
}

const corpus = [
  'Abbadon',
  'Abraxas',
  'Adramalech',
  'Agrith-Naar',
  'Ahpuch',
  'Ahriman',
  'Aku',
  'Alastair',
  'Alastor',
  'Algaliarept',
  'Alichino',
  'Amaimon',
  'Amon',
  'Andariel',
  'Andromeda',
  'Angel',
  'Antlia',
  'Anyanka',
  'Anzu',
  'Apollyon',
  'Apus',
  'Aquarius',
  'Aquila',
  'Ara',
  'Archimonde',
  'Aries',
  'Artery',
  'Asmodeus',
  'Astaroth',
  'Asura',
  'Auriga',
  'Azal',
  'Azazeal',
  'Azazel',
  'Azmodan',
  'Azura',
  'Baal',
  'Baalberith',
  'Babau',
  'Bacarra',
  "Bal'lak",
  'Balaam',
  'Balor',
  'Balrog',
  'Balthazar',
  'Baphomet',
  'Barakiel',
  'Barbariccia',
  'Barbas',
  'Bartimaeus',
  'Bast',
  "Bat'Zul",
  "Be'lakor",
  'Beastie',
  'Bebilith',
  'Beelzebub',
  'Behemoth',
  'Beherit',
  'Beleth',
  'Belfagor',
  'Belial',
  'Belphegor',
  'Belthazor',
  'Berry',
  'Betelguese',
  'Bile',
  'Blackheart',
  'Boötes',
  'Cacodemon',
  'Cadaver',
  'Caelum',
  'Cagnazzo',
  'Calcabrina',
  'Calcifer',
  'Camelopardalis',
  'Cancer',
  'Canes Venatici',
  'Canis Major',
  'Canis Minor',
  'Capricornus',
  'Carina',
  'Cassiopeia',
  'Castor',
  'Centaurus',
  'Cepheus',
  'Cetus',
  'Chamaeleon',
  'Chemosh',
  'Chernabog',
  'Cherry',
  'Cimeries',
  'Circinus',
  'Ciriatto',
  'Claude',
  'Columba',
  'Coma Berenices',
  'Cordelia',
  'Corona Austrina',
  'Corona Borealis',
  'Corvus',
  'Coyote',
  'Crater',
  'Crawly',
  'Crowley',
  'Crux',
  'Cryto',
  'Cyberdemon',
  'Cygnus',
  "D'Hoffryn",
  'Dabura',
  'Dagon',
  'Damballa',
  'Dante',
  'Darkseid',
  'Decarbia',
  'Delphinus',
  'Delrith',
  'Demogorgon',
  'Demonita',
  'Devi',
  'Diablo',
  'Diabolus',
  'Dorado',
  'Doviculus',
  'Doyle',
  'Draco',
  'Dracula',
  'Draghinazzo',
  'Dretch',
  'Dumain',
  'Duriel',
  'Emma',
  'Equuleus',
  'Eridanus',
  'Errtu',
  'Etna',
  'Etrigan',
  'Euronymous',
  'Faquarl',
  'Farfarello',
  'Femur',
  'Fenriz',
  'Firebrand',
  'Fornax',
  'Freddy',
  'Furfur',
  'Gaap',
  'Gary',
  'Gemini',
  'Glabrezu',
  'Gorgo',
  'Gothmog',
  'Gregor',
  'Grus',
  'Haborym',
  'Hades',
  'Halfrek',
  "Har'lakk",
  'Hastur',
  'Hecate',
  'Hell',
  'Hellboy',
  'Hercules',
  'Hex',
  'Hezrou',
  'Hiei',
  'Him',
  'Hnikarr',
  'Horologium',
  'Hot',
  'Hydra',
  'Hydrus',
  'Illa',
  'Indus',
  'Infernal',
  'Inferno',
  'Ishtar',
  'Jabor',
  'Jadis',
  'Janemba',
  'Japhrimel',
  'Jennifer',
  'Jormungandr',
  'Juiblex',
  "K'ril",
  "Kal'Ger",
  'Kali',
  'Khorne',
  "Kil'jaeden",
  'Kneesocks',
  'Koakuma',
  'Korrok',
  'Kronos',
  'Lacerta',
  'Laharl',
  'Lamia',
  'Leo Minor',
  'Leo',
  'Lepus',
  'Leviathan',
  'Libicocco',
  'Libra',
  'Ligur',
  'Lilith',
  'Little',
  'Loki',
  'Longhorn',
  'Lorne',
  'Lucifer',
  'Lupus',
  'Lynx',
  'Lyra',
  "Mal'Ganis",
  'Malacoda',
  'Maledict',
  'Malfegor',
  'Malice',
  'Mammon',
  'Mancubus',
  'Mania',
  'Mannoroth',
  'Mantus',
  'Marduk',
  'Marilith',
  'Masselin',
  'Mastema',
  'Meg',
  'Mehrunes',
  'Melek',
  'Melkor',
  'Mensa',
  'Mephisto',
  'Mephistopheles',
  'Metztli',
  'Microscopium',
  'Mictian',
  'Milcom',
  'Moloch',
  'Monoceros',
  'Mormo',
  'Musca',
  "N'zall",
  'Naamah',
  'Nadia',
  'Nalfeshnee',
  'Nanatoo',
  'Nergal',
  'Nero',
  'Neuro',
  'Newt',
  'Nihasa',
  'Nija',
  'Norma',
  'Nosferatu',
  'Nouda',
  'Nurgle',
  'Octans',
  'Ophiuchus',
  'Orion',
  'Ouroboros',
  'Overlord',
  'Oyashiro',
  'Pavo',
  'Pazuzu',
  'Pegasus',
  'Pennywise',
  'Persephone',
  'Perseus',
  'Phoenix',
  'Pictor',
  'Pisces',
  'Piscis Austrinus',
  'Psaro',
  'Puppis',
  'Pwcca',
  'Pwyll',
  'Pyxis',
  'Quasit',
  'Queezle',
  'Qwan',
  'Qweffor',
  'Ra',
  'Rakdos',
  'Ramuthra',
  'Randall',
  'Red',
  'Reticulum',
  'Retriever',
  'Rimmon',
  'Rin',
  'Ronove',
  'Rosier',
  'Rubicante',
  'Ruby',
  'Sabazios',
  'Sagitta',
  'Sagittarius',
  'Samael',
  'Samnu',
  'Satan',
  'Satanas',
  'Sauron',
  'Scanty',
  'Scarlet',
  'Scarmiglione',
  'Scorpius',
  'Sculptor',
  'Scumspawn',
  'Scutum',
  'Sebastian',
  'Sedit',
  'Sekhmet',
  'Sephiroth',
  'Serpens',
  'Set',
  'Sextans',
  'Shaitan',
  'Shax',
  'Shiva',
  'Silitha',
  'Slaanesh',
  'Sparda',
  'Spawn',
  'Spike',
  'Spine',
  'Straga',
  'Supay',
  "T'an-mo",
  'Taurus',
  'Taus',
  'Tchort',
  'Telescopium',
  'Tempus',
  'Tezcatlipoca',
  'Thammaron',
  'Thamuz',
  'Thoth',
  'Tiamat',
  "To'Kash",
  'Toby',
  'Triangulum Australe',
  'Triangulum',
  'Trigon',
  'Tucana',
  'Tunrida',
  'Turok-Han',
  'Typhon',
  'Tzeentch',
  'Ungoliant',
  'Ursa Major',
  'Ursa Minor',
  'Vein',
  'Vela',
  'Vergil',
  'Violator',
  'Virgo',
  'Volans',
  'Vrock',
  'Vulgrim',
  'Vulpecula',
  'Vyers',
  'Ware',
  'Wormwood',
  'Yaksha',
  'Yama',
  'Yaotzin',
  'Yen',
  "Yk'Lagor",
  'Zankou',
  'Zepar',
  'Zuul'
]
const ng = NameGenerator.initialize(corpus)

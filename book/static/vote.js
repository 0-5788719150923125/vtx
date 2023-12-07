const textBlocks = document.querySelectorAll('.markdown')
const blockSize = 64
let locked = false

function throttle(callback, delay) {
    let lastExecution = 0

    return function (event) {
        const now = new Date().getTime()

        if (now - lastExecution >= delay) {
            callback(event)
            lastExecution = now
        }
    }
}

// let previousNode
// let previousText

// let running = false
// const throttledMouseMove = throttle(function (event) {
//     try {
//         if (locked) return

//         console.clear()

//         // Get the character index under the mouse cursor
//         const mouseX = event.clientX
//         const mouseY = event.clientY


//         // const range = document.createRange();
//         // const node = range.selectNode(document.elementFromPoint(mouseX, mouseY));

//         const selection = document.caretPositionFromPoint(mouseX, mouseY)

//         const targetNode = selection.offsetNode
//         if (!targetNode.data) return

//         const cursorIndex = selection.offset

//         if (!selection.offsetNode?.parentNode) return

//         let originalText = targetNode.data

//         if (previousNode && previousText) {
//             previousNode.innerHTML = previousText
//         }

//         previousNode = selection.offsetNode?.parentNode
//         previousText = selection.offsetNode?.data
        
//         if (!previousNode) return

//         const previousSibling = selection.offsetNode.parentNode.previousSibling

//         let start = 0
//         if (selection.offset > blockSize) {
//             start = start + (selection.offset - blockSize)
//         }
//         if (previousSibling !== null) {
//             let remaining = blockSize - selection.offset
//             let length = previousSibling.previousSibling?.innerText.length
//             let sib = previousSibling.previousSibling?.innerText.slice(
//                 length - remaining,
//                 length
//             )
//         }

//         const textToHighlight = targetNode.data.slice(start, cursorIndex)

//         // // Find the index where your desired substring starts and ends
//         const startIndex = targetNode.data.indexOf(textToHighlight)
//         const endIndex = startIndex + textToHighlight.length

//         // // Split the original text into three parts: before, within, and after the target substring
//         const beforeText = originalText.slice(0, startIndex)
//         const withinText = originalText.slice(startIndex, endIndex)
//         const afterText = originalText.slice(endIndex)

//         selection.offsetNode.parentNode.innerHTML = `${beforeText}<span class="destroyed">${withinText}</span>${afterText}`
//     } catch (err) {
//         console.error(err)
//     }
// }, 50)

// textBlocks.forEach((textBlock) => {
//     textBlock.addEventListener('click', (event) => {
//         locked = true
//     })
//     textBlock.addEventListener('mousemove', throttledMouseMove)
// })

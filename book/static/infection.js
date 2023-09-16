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

let running = false
const throttledMouseMove = throttle(function (event) {
    try {
        if (locked) return

        running = true

        console.log('running again')

        // Get the character index under the mouse cursor
        const mouseX = event.clientX
        const mouseY = event.clientY

        const selection = document.caretPositionFromPoint(mouseX, mouseY)

        const targetNode = selection.offsetNode
        if (!targetNode.data) return

        console.info(selection)

        const cursorIndex = selection.offset

        if (!selection.offsetNode?.parentNode) return

        let originalText = targetNode.data
        // if (previousText) {
        //     originalText = previousText
        // }

        if (previousNode && previousText) {
            previousNode.innerHTML = previousText
        }

        previousNode = selection.offsetNode?.parentNode
        previousText = selection.offsetNode?.data

        if (!previousNode) return

        const previousSibling = selection.offsetNode.parentNode.previousSibling

        let start = 0
        if (selection.offset > blockSize) {
            start = start + (selection.offset - blockSize)
        }
        if (previousSibling !== null) {
            const previousSiblingText =
                previousSibling.previousSibling?.innerText
            if (previousSibling !== null) {
                let remaining = blockSize - selection.offset
                let length = previousSiblingText.length
                let sib = previousSibling.previousSibling.innerText.slice(
                    length - remaining,
                    length
                )
                console.log(sib)
            }
        }

        const textToHighlight = targetNode.data.slice(start, cursorIndex)
        // console.log(targetNode)
        console.log(textToHighlight)

        // // Find the index where your desired substring starts and ends
        const startIndex = targetNode.data.indexOf(textToHighlight)
        const endIndex = startIndex + textToHighlight.length

        // // Split the original text into three parts: before, within, and after the target substring
        const beforeText = originalText.slice(0, startIndex)
        const withinText = originalText.slice(startIndex, endIndex)
        const afterText = originalText.slice(endIndex)

        selection.offsetNode.parentNode.innerHTML = `${beforeText}<span class="destroyed">${withinText}</span>${afterText}`
        console.clear()
    } catch (err) {
        console.error(err)
    }
    running = false
}, 50)

let previousNode
let previousText
textBlocks.forEach((textBlock) => {
    textBlock.addEventListener('click', (event) => {
        locked = true
    })
    textBlock.addEventListener('mousemove', throttledMouseMove)
})

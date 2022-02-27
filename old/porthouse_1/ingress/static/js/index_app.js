
var globalData = {
    cake: 'Cherry'
    , clientId: -1
}

var cut = function(selector) {
    return $(selector).remove().html()
}

const Headers = {
    template: cut('.templates .headers')
    , data() {
        return {
            headers: {
                to: undefined,
                other: 'pre-defined'
            }
        }
    }
}


const Client = {
    template: cut('.templates .client')

    , props: [
        'initial',
    ]

    , data(){
        return {
            global: index_app.global
            , defaultUrl: 'ws://localhost:8000/'
            , liveUrl: undefined
            , messages: []
            , connected: false
            , messageText: 'current'
            , headerText: 'other: pre-defined\nto:room,other'
        }
    }

    , mounted(){
        this.liveUrl = this.url
        events.on('request-connect', this.requestConnect.bind(this))
        events.on('request-disconnect', this.disconnectSocket.bind(this))
        events.on('request-send', this.sendSocket.bind(this))
        events.on('request-clear', this.requestClear.bind(this))
    }

    , computed: {

        url() {
            return this.liveUrl || this.defaultUrl
        }
    }

    , methods: {

        sendSlot() {
            send(this.$slots.default()[0].children)
        }

        , createSocket(){
            // this.messages.push('Creating Socket')
            this.pushMessage('creating', undefined, 'createSocket')
            let ws = new WebSocket(this.url)
            ws.onmessage = this.onmessage.bind(this)
            ws.onopen = this.onopen.bind(this)
            ws.onerror = this.onerror.bind(this)
            ws.onclose = this.onclose.bind(this)
            this.ws = ws;
        }

        , disconnectSocket(){
            this.ws.close()
        }

        , requestClear() {
            this.messages = []
        }

        , onmessage(ev){
            // this.messages.push({
            //     direction: 'down'
            //     , type: 'onmessage'
            //     , value: ev.data
            // })

            this.pushMessage(ev.data, 'down', 'onmessage')

        }

        , onopen(ev){
            this.connected = true
            // this.messages.push('onopen')
            this.pushMessage('opened', undefined, 'onopen')
        }

        , onerror(ev){
            // this.messages.push('onerror')
            this.pushMessage(ev.data, undefined, 'onerror')
        }

        , onclose(ev){
            this.connected = false
            // this.messages.push('onclose')
            this.pushMessage('close')
        }

        , requestConnect(){
            if(!this.connected) {
                return this.createSocket()
            }

            this.pushMessage('already connected')
        }

        , pushMessage(value, direction, type, count=0) {

            let last = this.messages[this.messages.length-1]

            if(last
                && value == last.value
                && direction == last.direction) {
                last.count += 1
                return
            }

            this.messages.push({
                value, direction, type, count
            })

            // events.emit('requestConnect')
        }

        , sendSocket(ev) {
            this.sendText(ev.text)
        }

        , sendCurrent(){
            let msg = this.createHeadedPacket(this.messageText)
            this.sendText(msg)
            this.messageText = ''
        }

        , createHeadedPacket(text) {
            let h = [this.headerText, this.forcedHeaders()].join('\n')
            return `${h}\n\n${text}`
        }
        , forcedHeaders() {
            let dt = (new Date).toISOString()
            return `datetime: ${dt}\nforced: 0`
        }
        , sendText(text){
            this.ws.send(text)
            // this.messages.push({direction:'up', value:text})
            this.pushMessage(text, 'up')

        }

    }
}


// Define a new global component called button-counter
//app.component('ws-action', Action)

const IndexApp = {

    data() {
        console.log('IndexApp')
        return {
            counter: 0
            , global: globalData
            , clients: []
            , initCount: 10
            , messageText: 'apples'
        }
    }

    , mounted(){
        console.log('mounted')
        // events.on('request-connect', this.requestConnect.bind(this))

        // this.$bus.on('socket-message', this.socketMessage)
        this.mountClients()
    }

    , methods: {

        mountClients(){
            console.log('mountClients')
            for (var i = this.initCount - 1; i >= 0; i--) {
                this.clients.push({
                    index:i
                })
            }
        }
        , setCount(){
            this.clients = []
            this.addCount()
        }
        , addCount(){
            this.mountClients()
        }

        , socketMessage(event) {
            console.log('socketMessage', event)
            let content = this.getContent(event.data)
            let type = content.event

            let name  = `event_${type}`
            if(this[name]) {
                this[name](content, event)
            } else {
                console.warn('method', name, 'does not exist for content', content)
            }
        }

        , sendAll() {
            events.emit('request-send', { text: this.messageText})
        }

        , getContent(data) {
            let content = data
            try {
                content = JSON.parse(content)
                return content
            } catch(e){
                console.warn('Event data is not JSON', e)
            }
            return { 'text': content}
        }

        , requestConnect(){
            // this.createSocket()
            console.log('Emit request-connect')
            events.emit('request-connect')
        }

        , requestClear(){
            events.emit('request-clear')
        }

        , disconnectAll(){
            events.emit('request-disconnect')

        }
    }
}


App = Vue.createApp(IndexApp)
// App.config.globalProperties.$bus = events

App.component('client', Client)
App.component('headers', Headers)
indexApp = App.mount('#index_app')

console.log('Open')

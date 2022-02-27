
var globalData = {
    cake: 'Cherry'
    , clientId: -1
    , scenes: []
    , boundScenes: new Set()
}

var cut = function(selector) {
    return $(selector).remove().html()
}

const Action = {
    template: cut('.templates .ws-action-container')
    , data(){
        return {
            global: index_app.global
        }
    }
    , methods: {

        sendSlot() {
            send(this.$slots.default()[0].children)
        }
    }
}


// Define a new global component called button-counter
//app.component('ws-action', Action)

const IndexApp = {
    data() {
        return {
            counter: 0
            , currentMessage: ''
            , clientName: 'terry'
            , global: globalData
        }
    }
    , mounted(){
        this.$bus.on('socket-message', this.socketMessage)
    }
    , methods: {
        sendMessage(e){
            e.preventDefault()
            send(this.currentMessage)
            return false
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

        , event_welcome(content, event) {
            console.log('Welcome event.', content)
            this.global.clientId = content.id
            this.global.scenes = content.scenes
        }

        , event_NewWorld(content, event) {
            console.log('new world scene', content)
            if(this.global.scenes.indexOf(content.root) <= -1) {
                console.log('Storing', content.root)
                this.global.scenes.push(content.root)
            }
        }

        , event_bind_accept(content, event) {
            for(let scene of content.scenes) {
                this.global.boundScenes.add(scene)
            }
            // this.global.boundScenes.push(...content.scenes)

        }
        , event_scenes_disconnect(content, event){

            for(let sid of content.deleted) {
                let i = this.global.scenes.indexOf(sid)
                if(i == -1) {
                    continue
                }
                this.global.scenes.splice(i)
            }
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

        , sendForm(e) {
            e.preventDefault()
            console.log('Send form')
        }
    }
}

App = Vue.createApp(IndexApp)
App.config.globalProperties.$bus = events
App.component('ws-action', Action)
indexApp = App.mount('#index_app')



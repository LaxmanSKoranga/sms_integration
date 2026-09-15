<template>
  <div class="flex items-end gap-2 px-3 py-2.5 sm:px-10" v-bind="$attrs">
    <Textarea
      ref="textareaRef"
      v-model="content"
      type="textarea"
      class="min-h-8 w-full"
      :rows="rows"
      :placeholder="placeholder"
      @focus="rows = 3"
      @blur="rows = 1"
      @keydown.enter.stop="(e) => sendTextMessage(e)"
    />
    <Button variant="solid" :label="__('Send')" @click="sendSMSMessage" />
  </div>
</template>

<script setup>
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource, Textarea, Button, toast } from 'frappe-ui'
import { ref, nextTick } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const doc = defineModel({ type: Object, default: () => ({}) })
const sms = defineModel('sms', { type: Object, default: () => ({}) })

const { capture } = useTelemetry()

const rows = ref(1)
const textareaRef = ref(null)
const content = ref('')
const placeholder = ref(__('Type your message here...'))

function show() {
  nextTick(() => textareaRef.value.el.focus())
}

function sendTextMessage(event) {
  if (event.shiftKey) return
  sendSMSMessage()
  textareaRef.value.el?.blur()
}

function sendSMSMessage() {
  if (!content.value.trim()) return
  if (!doc.value.mobile_no) {
    toast.error(__('This record has no phone number to send an SMS to.'))
    return
  }
  let args = {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    to: doc.value.mobile_no,
    body: content.value,
  }
  content.value = ''
  createResource({
    url: 'sms_integration.sms.api.send_sms',
    params: args,
    auto: true,
    onSuccess: () => {
      capture('sms_send_message')
      sms.value.reload()
    },
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Failed to send SMS'))
    },
  })
}

defineExpose({ show })
</script>

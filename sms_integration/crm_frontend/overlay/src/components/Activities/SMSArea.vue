<template>
  <div>
    <div v-for="sms in messages" :key="sms.name" class="mb-3">
      <div
        v-if="sms.is_opt_out_event"
        class="mb-1 text-2xs text-ink-gray-4"
        :class="sms.direction == 'Outgoing' ? 'text-right pr-1' : 'text-left pl-1'"
      >
        {{ isStopKeyword(sms.body) ? __('Contact opted out') : __('Contact opted back in') }}
      </div>
      <div
        class="activity group flex gap-2"
        :class="sms.direction == 'Outgoing' ? 'flex-row-reverse' : ''"
      >
        <div
          class="group/message relative max-w-[90%] whitespace-pre-wrap rounded-md bg-surface-gray-1 p-1.5 pl-2 text-base text-ink-gray-9 shadow-sm"
        >
          <Badge
            v-if="['Failed', 'Undelivered'].includes(sms.status)"
            theme="red"
            :label="sms.status"
            class="absolute -top-2 right-0"
          />
          <div class="flex gap-2 justify-between">
            <div>{{ sms.body }}</div>
            <div class="-mb-1 flex shrink-0 items-end gap-1 text-ink-gray-5">
              <Tooltip :text="formatDate(sms.creation, 'ddd, MMM D, YYYY')">
                <div class="text-2xs">
                  {{ formatDate(sms.creation, 'hh:mm a') }}
                </div>
              </Tooltip>
              <div v-if="sms.direction == 'Outgoing'">
                <CheckIcon v-if="sms.status == 'Sent'" class="size-4" />
                <DoubleCheckIcon
                  v-else-if="sms.status == 'Delivered'"
                  class="size-4"
                  :class="{ 'text-ink-blue-5': sms.status == 'Delivered' }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/Icons/DoubleCheckIcon.vue'
import { formatDate } from '@/utils'
import { Tooltip, Badge } from 'frappe-ui'

defineProps({
  messages: { type: Array, default: () => [] },
})

const STOP_KEYWORDS = ['STOP', 'STOPALL', 'UNSUBSCRIBE', 'CANCEL', 'END', 'QUIT']

function isStopKeyword(body) {
  return STOP_KEYWORDS.includes((body || '').trim().toUpperCase())
}
</script>

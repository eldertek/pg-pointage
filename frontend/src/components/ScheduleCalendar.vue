<template>
  <v-card>
    <v-card-text>
      <v-row>
        <v-col cols="12">
          <v-sheet height="600">
            <v-calendar
              v-model="value"
              :weekdays="weekdays"
              :type="type"
              :events="events"
              :event-color="getEventColor"
              :first-time="firstTime"
              :interval-minutes="intervalMinutes"
              :interval-count="intervalCount"
              :interval-height="intervalHeight"
              @click:event="showEvent"
            >
              <template #event="{ event }">
                <div class="text-truncate">
                  {{ event.name }}
                </div>
              </template>
            </v-calendar>
          </v-sheet>
        </v-col>
      </v-row>
    </v-card-text>

    <!-- Dialog pour afficher les détails d'un événement -->
    <v-dialog v-model="selectedOpen" max-width="400">
      <v-card>
        <v-card-title>{{ selectedEvent ? selectedEvent.name : '' }}</v-card-title>
        <v-card-text>
          <div v-if="selectedEvent">
            <Text>Début: {{ formatTime(selectedEvent.start) }}</Text>
            <Text>Fin: {{ formatTime(selectedEvent.end) }}</Text>
            <Text>Type: {{ selectedEvent.type }}</Text>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="selectedOpen = false">{{ $t('common.close') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script>
import { Text } from '@/components/typography'

export default {
  name: 'ScheduleCalendar',
  components: {
    Text
  },
  
  props: {
    schedule: {
      type: Object,
      required: true
    }
  },

  data: () => ({
    type: 'week',
    weekdays: [1, 2, 3, 4, 5, 6, 0],
    value: '',
    events: [],
    selectedEvent: null,
    selectedOpen: false,
    firstTime: '06:00',
    intervalMinutes: 30,
    intervalCount: 32,
    intervalHeight: 40,
    colors: {
      workTime: '#00346E',
      break: '#F78C48',
      pause: '#4CAF50'
    }
  }),

  watch: {
    schedule: {
      immediate: true,
      handler: 'generateEvents'
    }
  },

  methods: {
    generateEvents() {
      if (!this.schedule || !this.schedule.details) return

      const events = []
      const now = new Date()
      const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay() + (now.getDay() === 0 ? -6 : 1)))

      this.schedule.details.forEach(detail => {
        const dayDate = new Date(startOfWeek)
        dayDate.setDate(dayDate.getDate() + (detail.day_of_week - 1))

        // Ajouter les périodes de travail
        if (detail.start_time_1 && detail.end_time_1) {
          events.push({
            name: 'Temps de travail',
            start: this.combineDateTime(dayDate, detail.start_time_1),
            end: this.combineDateTime(dayDate, detail.end_time_1),
            type: 'workTime',
            color: this.colors.workTime
          })
        }

        if (detail.start_time_2 && detail.end_time_2) {
          events.push({
            name: 'Temps de travail',
            start: this.combineDateTime(dayDate, detail.start_time_2),
            end: this.combineDateTime(dayDate, detail.end_time_2),
            type: 'workTime',
            color: this.colors.workTime
          })
        }

        // Ajouter la pause déjeuner si configurée
        if (this.schedule.break_duration && detail.start_time_1 && detail.end_time_2) {
          const breakStart = this.combineDateTime(dayDate, detail.end_time_1)
          const breakEnd = this.combineDateTime(dayDate, detail.start_time_2)
          events.push({
            name: 'Pause déjeuner',
            start: breakStart,
            end: breakEnd,
            type: 'break',
            color: this.colors.break
          })
        }
      })

      this.events = events
    },

    combineDateTime(date, timeStr) {
      const [hours, minutes] = timeStr.split(':')
      const combined = new Date(date)
      combined.setHours(parseInt(hours), parseInt(minutes), 0)
      return combined
    },

    getEventColor(event) {
      return event.color
    },

    showEvent({ event }) {
      this.selectedEvent = event
      this.selectedOpen = true
    },

    formatTime(date) {
      return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  }
}
</script>

<style scoped>
.v-calendar >>> .v-event {
  border-radius: 4px;
  padding: 2px 4px;
}
</style> 
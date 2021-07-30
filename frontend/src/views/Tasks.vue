<template>
  <div class="tasks">
    <top-bar title="Maintenance Tasks"></top-bar>
    <v-row v-if="jobDetails">
      <v-col cols="12">
        <v-expansion-panels>
          <v-expansion-panel v-for="key in jobs" :key="key">
            <v-expansion-panel-header>
              <v-row no-gutters>
                <v-col cols="2">
                  {{key}}
                </v-col>
                <v-col>
                  <div v-if="jobDetails[key]">
                    <v-icon small v-if="!jobDetails[key].success" color="deep-orange darken-3">mdi-alert-circle</v-icon>
                    <v-icon small v-else color="success">mdi-check-circle</v-icon>
                    Last: {{jobDetails[key].started | moment('YYYY-MM-DD HH:mm:ss')}}
                    <span v-if="jobDetails[key].scheduled">
                      | Next: {{jobDetails[key].scheduled | moment('YYYY-MM-DD HH:mm:ss')}}
                    </span>
                  </div>
                  <div v-else>
                      <v-icon color="blue-grey-darken-3">mdi-cancel</v-icon>
                  </div>
                </v-col>
                <v-col cols="2">
                  <v-btn small elevation="2" @click.stop="loadJobDetails(key)">
                    <v-icon>mdi-refresh</v-icon>
                  </v-btn>
                  <v-btn small elevation="2" 
                      @click.stop="startJob(key)"
                      :disabled="activeJobs[key] && activeJobs[key].status === 'started'"
                      :loader="activeJobs[key] && activeJobs[key].status === 'started'"
                      :class="taskButtonClass(key)"
                      >
                    <v-icon>mdi-play</v-icon> Run
                    <span v-if="activeJobs[key]">
                      ({{ activeJobs[key].meta.progress }})
                    </span>
                  </v-btn>
                </v-col>
              </v-row>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <template v-if="jobDetails[key]">
                <v-row dense>
                  <v-col cols="12">
                    <v-list-item two-line>
                      <v-list-item-content>
                        <v-list-item-title>{{jobDetails[key].job}}</v-list-item-title>
                        <v-list-item-subtitle>Job ID</v-list-item-subtitle>
                      </v-list-item-content>
                    </v-list-item>
                    <v-list-item two-line>
                      <v-list-item-content>
                        <v-list-item-title>{{jobDetails[key].started | moment('YYYY-MM-DD HH:mm:ss')}}</v-list-item-title>
                        <v-list-item-subtitle>Started</v-list-item-subtitle>
                      </v-list-item-content>
                    </v-list-item>
                    <v-list-item two-line>
                      <v-list-item-content>
                        <v-list-item-title>{{jobDetails[key].finished | moment('YYYY-MM-DD HH:mm:ss')}}</v-list-item-title>
                        <v-list-item-subtitle>Finished</v-list-item-subtitle>
                      </v-list-item-content>
                    </v-list-item>
                    <v-list-item two-line>
                      <v-list-item-content>
                        <v-list-item-title>{{jobDetails[key].scheduled | moment('YYYY-MM-DD HH:mm:ss')}}</v-list-item-title>
                        <v-list-item-subtitle>Next Scheduled Run</v-list-item-subtitle>
                      </v-list-item-content>
                    </v-list-item>
                    <template v-if="key==='ldap_sync_results'">
                      See <router-link to="/ldap">LDAP Status</router-link> for details
                    </template>
                    <template v-if="key==='check_quotas'">
                      <v-list-item two-line>
                        <v-list-item-content>
                          <v-list-item-title>{{jobDetails[key].updated}}</v-list-item-title>
                          <v-list-item-subtitle>Updated</v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-line>
                        <v-list-item-content>
                          <v-list-item-title>{{jobDetails[key].total_space | prettyBytes()}}</v-list-item-title>
                          <v-list-item-subtitle>Total Space Used</v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </template>
                    <template v-if="key==='expire_images'">
                      <v-list-item two-line>
                        <v-list-item-content>
                          <v-list-item-title>{{jobDetails[key].updated}}</v-list-item-title>
                          <v-list-item-subtitle>Deleted</v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-line>
                        <v-list-item-content>
                          <v-list-item-title>{{jobDetails[key].space_reclaimed | prettyBytes()}}</v-list-item-title>
                          <v-list-item-subtitle>Total Space Freed</v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </template>
                  </v-col>
                </v-row>
                <v-row dense v-if="!jobDetails[key].success">
                  <v-col cols="12" class="yellow lighten-4">
                    <h3 class="red--text darken-1--text">Exception</h3>
                    <pre><code>{{jobDetails[key].exception}}</code></pre>
                  </v-col>
                </v-row>
              </template>
              <template v-else>
                <em>This job didn't run yet</em>
              </template>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { each as _each } from 'lodash';
import { AdmKey, Job } from '@/store/models';

interface State {
  jobs: string[];
}

export default Vue.extend({
  name: 'Tasks',
  mounted() {
    _each(this.jobs, key => this.loadJobDetails(key));
  },
  computed: {
    jobs() {
      return this.$store.getters['adm/slots'];
    },
    jobDetails() {
      return this.$store.getters['adm/admKeys'];
    },
    activeJobs() {
      return this.$store.getters['adm/activeJobs'];
    },
  },
  watch: {
    activeJobs: function(newJobs, oldJobs) {
      _each(newJobs, (job: Job, key: string) => {
        if (oldJobs[key] !== null && oldJobs[key].id === newJobs[key].id) {
          return;
        }
        if (job !== null && job.status !== 'finished' && job.status !== 'failed') {
          const pollJob = () => {
            this.$store.dispatch('adm/taskStatus', key)
              .then(res => {
                if (res.status !== 'finished' && res.status !== 'failed') {
                  setTimeout(pollJob, 1000);
                }
                else {
                  this.loadJobDetails(key);
                }
              })
              .catch(err => this.$store.commit('snackbar/showError', err));
          };
          setTimeout(pollJob, 50);
        }
      })
    }
  },
  methods: {
    loadJobDetails(key: string) {
      this.$store.dispatch('adm/admResults', key)
        .catch(err => {
          if (!err.response || err.response.status !== 404) {
            this.$store.commit('snackbar/showError', err);
          }
        });
    },
    startJob(key: string) {
      this.$store.dispatch('adm/runTask', key)
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
    taskButtonClass(key: string) {
      return { 
        'green lighten-1': this.activeJobs[key]?.status === 'finished', 
        'red lighten-1': this.activeJobs[key]?.status === 'failed' 
      }
    },
  }
});
</script>
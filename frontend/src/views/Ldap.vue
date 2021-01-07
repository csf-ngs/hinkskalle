<template>
  <div class="ldap">
    <top-bar title="LDAP Administration"></top-bar>
    <v-container v-if="ldap && ldap.status=='configured'">
      <v-row>
        <v-col cols="12" md="5" offset-md="1">
          <h2>Config</h2>
          <v-list-item two-line>
            <v-list-item-content>
              <v-list-item-title>{{ldap.config['HOST']}}</v-list-item-title>
              <v-list-item-subtitle>Host</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <v-list-item two-line>
            <v-list-item-content>
              <v-list-item-title>{{ldap.config['PORT']}}</v-list-item-title>
              <v-list-item-subtitle>Port</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <v-list-item two-line>
            <v-list-item-content>
              <v-list-item-title>{{ldap.config['BIND_DN']}}</v-list-item-title>
              <v-list-item-subtitle>Bind DN</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <v-list-item two-line>
            <v-list-item-content>
              <v-list-item-title>{{ldap.config['BASE_DN']}}</v-list-item-title>
              <v-list-item-subtitle>Search Base</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
        </v-col>
        <v-col cols="12" md="5">
          <h2>Test</h2>
          <v-alert
            elevation="2"
            colored-border
            border="left"
            :color="pingColor"
            :icon="pingIcon"
          >
            <v-row no-gutters>
              <v-col class="grow">
                <h3>{{pingResult ? pingResult.status : ''}}</h3>
              </v-col>
              <v-spacer></v-spacer>
              <v-col class="shrink">
                <v-btn small id="ping" @click="ping()">Ping Server</v-btn>
              </v-col>
            </v-row>
            <v-row v-if="pingResult && pingResult.error">
              <v-col>{{pingResult.error}}</v-col>
            </v-row>
          </v-alert>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <div class="d-flex justify-space-between">
            <h2>Synchronisation</h2>
            <v-btn small id="sync" @click="startSync()">Trigger Sync</v-btn>
          </div>

          <v-alert
            v-if="ldapSyncJob"
            elevation="2"
            colored-border
            border="left"
            :color="ldapSyncColor"
            :icon="ldapSyncIcon"
            v-model="showSyncProgress"
            dismissible
          >
            <v-row dense>
              <v-col>
                <h3>Syncing...</h3>
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title>{{ldapSyncJob.id}}</v-list-item-title>
                    <v-list-item-subtitle>Job ID</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title>{{ldapSyncJob.status}}</v-list-item-title>
                    <v-list-item-subtitle>Status</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title>
                      <span v-if="ldapSyncJob.startedAt">
                        {{ldapSyncJob.startedAt | moment('YYYY-MM-DD HH:mm:ss')}}
                      </span>
                      <span v-else>
                        -
                      </span>
                    </v-list-item-title>
                    <v-list-item-subtitle>Started At</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title>
                      <span v-if="ldapSyncJob.meta">
                        {{ldapSyncJob.meta.progress}}
                        <span v-if="ldapSyncJob.meta.progress == 'done'">
                          - finished {{ldapSyncJob.endedAt | moment('YYYY-MM-DD HH:mm:ss')}}
                        </span>
                      </span>
                      <span v-else>
                        -
                      </span>
                    </v-list-item-title>
                    <v-list-item-subtitle>Progress</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
              </v-col>
            </v-row>
          </v-alert>

          <v-container fluid v-if="ldapSyncResults">
            <v-row dense>
              <v-col cols="12">
                <div class="d-flex justify-space-between">
                  <h3>Latest Sync</h3>
                  <v-btn small icon @click="loadSyncResults()"><v-icon>mdi-refresh</v-icon></v-btn>
                </div>
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title>{{ldapSyncResults.job}}</v-list-item-title>
                    <v-list-item-subtitle>Job ID</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title>{{ldapSyncResults.started | moment('YYYY-MM-DD HH:mm:ss')}}</v-list-item-title>
                    <v-list-item-subtitle>Started</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item two-line>
                  <v-list-item-content>
                    <v-list-item-title>{{ldapSyncResults.finished | moment('YYYY-MM-DD HH:mm:ss')}}</v-list-item-title>
                    <v-list-item-subtitle>Finished</v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
              </v-col>
            </v-row>
            <v-row dense>
              <v-col cols="12">
                <v-expansion-panels>
                  <v-expansion-panel :disabled="ldapSyncResults.synced.length==0">
                    <v-expansion-panel-header>
                      Success ({{ldapSyncResults.synced.length}})
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <v-list dense>
                        <v-list-item v-for="username in ldapSyncResults.synced" :key="username">
                          <router-link :to="{ name: 'Users', query: { id: username }}">{{username}}</router-link>
                        </v-list-item>
                      </v-list>
                    </v-expansion-panel-content>
                  </v-expansion-panel>
                  <v-expansion-panel :disabled="ldapSyncResults.conflict.length==0">
                    <v-expansion-panel-header>
                      Conflict ({{ldapSyncResults.conflict.length}})
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <v-list dense>
                        <v-list-item v-for="username in ldapSyncResults.conflict" :key="username">
                          <router-link :to="{ name: 'Users', query: { id: username }}">{{username}}</router-link>
                        </v-list-item>
                      </v-list>
                    </v-expansion-panel-content>
                  </v-expansion-panel>
                  <v-expansion-panel :disabled="ldapSyncResults.failed.length==0">
                    <v-expansion-panel-header>
                      Failed ({{ldapSyncResults.failed.length}})
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <v-list dense>
                        <v-list-item v-for="username in ldapSyncResults.failed" :key="username">
                          <router-link :to="{ name: 'Users', query: { id: username }}">{{username}}</router-link>
                        </v-list-item>
                      </v-list>
                    </v-expansion-panel-content>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-col>
            </v-row>
          </v-container>
        </v-col>
      </v-row>
    </v-container>
    <v-container v-else>
      <h4>Not Configured (why are you seeing me?)</h4>
    </v-container>
  </div>
</template>
<script lang="ts">
import { LdapStatus, LdapPing, AdmLdapSyncResults, Job } from '@/store/models';
import Vue from 'vue';

export default Vue.extend({
  name: 'Ldap',
  mounted() {
    this.loadStatus();
    this.loadSyncResults();
  },
  data: () => ({
    showSyncProgress: false,
  }),
  computed: {
    loading(): boolean {
      return this.$store.getters['adm/status'] === 'loading';
    },
    ldap(): LdapStatus | null {
      return this.$store.getters['adm/ldapStatus'];
    },
    pingResult(): LdapPing | null {
      return this.$store.getters['adm/ldapPing'];
    },
    pingColor(): string {
      return !this.pingResult ? '' 
        : this.pingResult.status === 'ok' ? 'success lighten-1'
        : 'error lighten-1';
    },
    pingIcon(): string | null {
      return !this.pingResult ? null
        : this.pingResult.status === 'ok' ? 'mdi-check-circle'
        : 'mdi-alert-circle'
    },
    ldapSyncResults(): AdmLdapSyncResults | null {
      return this.$store.getters['adm/ldapSyncResults'];
    },
    ldapSyncJob(): Job | null {
      return this.$store.getters['adm/ldapSyncJob'];
    },
    ldapSyncColor(): string {
      return !this.ldapSyncJob || this.ldapSyncJob.status === 'queued' ? ''
        : this.ldapSyncJob.status === 'started' ? 'indigo lighten-1' 
        : this.ldapSyncJob.status === 'finished' ? 'success lighten-1'
        : this.ldapSyncJob.status === 'failed' ? 'error lighten-1'
        : this.ldapSyncJob.status === 'deferred' ? 'warning lighten-1'
        : 'grey lighten-1'
    },
    ldapSyncIcon(): string | null {
      return !this.ldapSyncJob ? null
        : this.ldapSyncJob.status === 'queued' ? 'mdi-timer-sand' 
        : this.ldapSyncJob.status === 'started' ? 'mdi-run' 
        : this.ldapSyncJob.status === 'finished' ? 'mdi-check-circle'
        : this.ldapSyncJob.status === 'failed' ? 'mdi-alert-circle'
        : this.ldapSyncJob.status === 'deferred' ? 'mdi-sleep'
        : 'mdi-progress-question';
    },
  },
  methods: {
    loadStatus() {
      this.$store.dispatch('adm/ldapStatus')
        .catch(err => this.$store.commit('snackbar/showError', err))
    },
    ping() {
      this.$store.dispatch('adm/ldapPing')
        .catch(err => this.$store.commit('snackbar/showError', err))
    },
    loadSyncResults() {
      this.$store.dispatch('adm/ldapSyncResults')
        .catch(err => this.$store.commit('snackbar/showError', err))
    },
    startSync() {
      this.showSyncProgress = true;
      this.$store.dispatch('adm/syncLdap')
        .then(res => {
          const pollLdapJob = () => {
            this.$store.dispatch('adm/syncLdapStatus')
              .then(res => {
                if (res.status !== 'finished' && res.status !== 'failed') {
                  setTimeout(pollLdapJob, 1000);
                }
                else if (res.status === 'finished') {
                  this.loadSyncResults();
                }
              })
              .catch(err => this.$store.commit('snackbar/showError', err))
          };
          setTimeout(pollLdapJob, 1000);
        })
        .catch(err => this.$store.commit('snackbar/showError', err));
    }
  }
});
</script>
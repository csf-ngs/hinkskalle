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
    </v-container>
    <v-container v-else>
      <h4>Not Configured (why are you seeing me?)</h4>
    </v-container>
  </div>
</template>
<script lang="ts">
import { LdapStatus, LdapPing } from '@/store/models';
import Vue from 'vue';

export default Vue.extend({
  name: 'Ldap',
  mounted() {
    this.loadStatus();
  },
  computed: {
    loading(): boolean {
      return this.$store.getters['adm/status'] === 'loading';
    },
    ldap(): LdapStatus {
      return this.$store.getters['adm/ldapStatus'];
    },
    pingResult(): LdapPing {
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


    }
  },
  methods: {
    loadStatus() {
      this.$store.dispatch('adm/ldapStatus')
        .catch(err => this.$store.commit('snackbar/showError', err))
    },
    ping() {
      this.$store.dispatch('adm/ldapPing')
        .catch(err => this.$store.commit('snackbar/showError', err))
    }
  }
});
</script>
<template>
  <div class="ldap">
    <top-bar title="LDAP Administration"></top-bar>
    <v-container v-if="ldap && ldap.status=='configured'">
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
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
      </v-row>
    </v-container>
    <v-container v-else>
      <h4>Not Configured (why are you seeing this?)</h4>
    </v-container>
  </div>
</template>
<script lang="ts">
import { LdapStatus } from '@/store/models';
import Vue from 'vue';

export default Vue.extend({
  name: 'Ldap',
  mounted() {
    this.loadStatus();
  },
  computed: {
    ldap(): LdapStatus {
      return this.$store.getters['adm/ldapStatus'];
    },
  },
  methods: {
    loadStatus() {
      this.$store.dispatch('adm/ldapStatus')
        .catch(err => this.$store.commit('snackbar/showError', err))
    },
  }
});
</script>
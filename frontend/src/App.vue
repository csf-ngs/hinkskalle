<template>
  <v-app>
    <v-navigation-drawer app expand-on-hover dark class="green darken-3">
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title class="title text-uppercase">
            Hinkskalle
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-divider></v-divider>
      <v-list dense nav>
        <template v-if="isLoggedIn">
          <v-list-item link :to="'/account'">
            <v-list-item-icon><v-icon>mdi-account</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>{{currentUser.fullname}}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item link :to="'/tokens'">
            <v-list-item-icon><v-icon>mdi-key-chain-variant</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Tokens</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </template>
        <v-list-item link v-else color="error" :to="'/login'">
          <v-list-item-icon><v-icon>mdi-alert</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Not Logged In</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
      <template v-if="currentUser && currentUser.isAdmin">
        <v-divider></v-divider>
        <v-list dense nav>
          <v-list-item link :to="'/users'" id="user-admin">
            <v-list-item-icon><v-icon>mdi-account-cog-outline</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>User Administration</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item link :to="'/ldap'" id="ldap-admin" v-if="ldapStatus && ldapStatus.status=='configured'">
            <v-list-item-icon><v-icon>mdi-account-search-outline</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>LDAP Administration</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </template>
      <v-divider></v-divider>
      <v-list dense nav>
        <v-list-item link :to="'/'">
          <v-list-item-icon><v-icon>mdi-home</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Home</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <template v-if="isLoggedIn">
          <v-list-item link :to="'/entities'">
            <v-list-item-icon><v-icon>mdi-account-box-multiple</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Entities</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          <v-list-item link :to="'/collections'">
            <v-list-item-icon><v-icon>mdi-folder-multiple</v-icon></v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>Your Collections</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </template>
      </v-list>
      <template v-slot:append v-if="isLoggedIn">
        <v-list dense nav>
        <v-list-item link @click="logout">
          <v-list-item-icon><v-icon>mdi-power</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        </v-list>
      </template>
    </v-navigation-drawer>

    <v-main>
      <router-view></router-view>
    </v-main>
    <v-snackbar v-model="showSnackbar" :timeout="snackbarTimeout" rounded="pill" :color="snackbarColor">
      <template v-slot:action="{ attrs }">
        <v-btn id="close-snackbar" icon @click="hideSnackbar()" v-bind="attrs">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </template>
      {{snackbarMsg}}
    </v-snackbar>
  </v-app>
</template>

<script lang="ts">
import { AxiosError } from 'axios';
import Vue from 'vue';
import { LdapStatus, User } from './store/models';

import { SnackbarType } from './store/modules/snackbar';

export default Vue.extend({
  name: 'App',
  created: function () {
    const { $store, $router } = this;
    this.$store.commit('registerInterceptor', (err: AxiosError) => {
      return new Promise((resolve, reject) => {
        if (err.response && err.response.status === 401 && err.config) {
          $store.dispatch('logout');
          if ($router.currentRoute.fullPath !== '/login') {
            $router.push('/login');
          }
        }
        throw err;
      });
    });
    this.$store.dispatch('adm/ldapStatus')
      .catch(err => {
        this.$store.commit('snackbar/showError', err);
      });
  },
  computed: {
    isLoggedIn(): boolean {
      return this.$store.getters.isLoggedIn;
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    showSnackbar: {
      get: function(): boolean {
        return this.$store.getters['snackbar/show'];
      },
      set: function(newValue: boolean) {
        if (!newValue) {
          this.$store.commit('snackbar/close');
        }
      },
    },
    snackbarMsg(): string {
      return this.$store.getters['snackbar/msg'];
    },
    snackbarColor(): string {
      const type: SnackbarType = this.$store.getters['snackbar/type'];
      const map: { [key: string]: string } = {
        '': 'blue-grey',
        'info': 'blue-grey',
        'success': 'success',
        'error': 'error',
      };
      return map[type];
    },
    snackbarTimeout(): number {
      return this.$store.getters['snackbar/type'] === 'error' ? -1 : 5000;
    },
    ldapStatus(): LdapStatus {
      return this.$store.getters['adm/ldapStatus'];
    },
  },
  methods: {
    hideSnackbar() {
      this.$store.commit('snackbar/close');
    },
    logout() {
      this.$store.dispatch('logout')
        .then(() => this.$router.push('/login'));
    }
  }
});
</script>

<style>
span.v-badge--inline i.v-icon {
  margin-right: -5px;
}
</style>
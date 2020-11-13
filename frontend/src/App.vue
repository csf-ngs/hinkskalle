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
            <v-list-item-icon><v-icon>mdi-lock-open</v-icon></v-list-item-icon>
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
      <v-divider></v-divider>
      <v-list dense nav>
        <v-list-item link :to="'/'">
          <v-list-item-icon><v-icon>mdi-home</v-icon></v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Home</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-list-item link :to="'/collections'">
        <v-list-item-icon><v-icon>mdi-view-list</v-icon></v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>Collections</v-list-item-title>
        </v-list-item-content>
        </v-list-item>
      </v-list>
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
import Vue from 'vue';
import { User } from './store/models';

export default Vue.extend({
  name: 'App',
  created: function () {
    const { $store, $router } = this;
    this.$store.commit('registerInterceptor', (err) => {
      return new Promise((resolve, reject) => {
        if (err.response && err.response.status === 401 && err.config && !err.config.__isRetryRequest) {
          $store.dispatch('logout');
          $router.push('/login');
        }
        throw err;
      });
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
      const type = this.$store.getters['snackbar/type'];
      const map = {
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
  },
  methods: {
    hideSnackbar() {
      this.$store.commit('snackbar/close');
    },
  }
});
</script>

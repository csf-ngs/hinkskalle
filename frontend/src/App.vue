<template>
  <v-app>
    <v-app-bar app>
      <v-toolbar-title class="headline text-uppercase">
        <span>Hinkskalle</span>
      </v-toolbar-title>
      <v-toolbar-items>
        <v-btn text @click="$router.push('/')">Home</v-btn>
      </v-toolbar-items>
      <v-spacer></v-spacer>
      <v-btn v-if="isLoggedIn" text>
        {{currentUser.fullname}}
        <v-icon right>mdi-account</v-icon>
      </v-btn>
      <v-btn v-else text color="error">
        Not Logged In
        <v-icon>mdi-alert</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view></router-view>
    </v-main>
    <v-snackbar v-model="showSnackbar" :timeout="1500" color="blue-grey lighten-1">
      {{snackbarMsg}}
      <v-btn id="close-snackbar" color="pink lighten-4" icon @click="hideSnackbar()">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-snackbar>
  </v-app>
</template>

<script lang="ts">
import Vue from 'vue';
import { User } from './store';

export default Vue.extend({
  name: 'App',
  computed: {
    isLoggedIn(): boolean {
      return this.$store.getters.isLoggedIn;
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    showSnackbar(): boolean {
      return this.$store.getters.showSnackbar;
    },
    snackbarMsg(): string {
      return this.$store.getters.snackbarMsg;
    },
  },
  methods: {
    hideSnackbar() {
      this.$store.commit('closeSnackbar');
    },
  }
});
</script>

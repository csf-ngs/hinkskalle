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
    <v-snackbar v-model="showSnackbar" :timeout="1500" rounded="pill" color="blue-grey">
      {{snackbarMsg}}
      <v-btn id="close-snackbar" color="pink lighten-1" icon @click="hideSnackbar()">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-snackbar>
  </v-app>
</template>

<script lang="ts">
import Vue from 'vue';
import { User } from './store/models';

export default Vue.extend({
  name: 'App',
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
  },
  methods: {
    hideSnackbar() {
      this.$store.commit('snackbar/close');
    },
  }
});
</script>

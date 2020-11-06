<template>
  <div class="home">
    <v-container>
      <v-layout wrap>
        <v-row justify="center">
          <v-col cols="6">
            <h1 class="display-1">Hello, Hinkskalle speaking!</h1>
          </v-col>
        </v-row>
      </v-layout>
      <v-row justify="center" v-if="!isLoggedIn">
        <v-col cols="6" id="login-msg">
          <v-card elevation="1" color="warning" :to="'/login'">
            <v-card-title>Not sure who you are! Please log in.</v-card-title>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';

export default Vue.extend({
  name: 'Home',
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
  },
  components: {
  },
});
</script>

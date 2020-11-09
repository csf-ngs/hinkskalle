<template>
  <div class="home">
    <v-container>
        <v-row justify="center">
          <v-col cols="6">
            <h1 class="display-1 text-center">Hello, Hinkskalle speaking!</h1>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <h3>Configuration</h3>
            <v-card tile>
              <v-card-title>
                Pull only:
              </v-card-title>
              <v-card-subtitle>No account necessary</v-card-subtitle>
              <v-card-text>
                <code class="grey white--text">
                  singularity remote add --nologin hinkskalle {{backendUrl}}
                  singularity remote use hinkskalle
                </code>
              </v-card-text>
            </v-card>
            <v-card tile>
              <v-card-title>
                Pull and push:
              </v-card-title>
              <v-card-subtitle>
                <span v-show="!isLoggedIn">Log in and</span> get a token
              </v-card-subtitle>
              <v-card-text>
                <code>
                  singularity remote add hinkskalle {{backendUrl}}
                  # paste token
                  # or
                  singularity remote login hinkskalle
                  singularity remote use hinkskalle
                </code>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      <v-row justify="center" v-if="!isLoggedIn">
        <v-col cols="6" id="login-msg">
          <v-card elevation="1" color="warning" :to="'/login'">
            <v-card-title><v-icon>mdi-login</v-icon> Not sure who you are! Please log in.</v-card-title>
          </v-card>
        </v-col>
      </v-row>
      <v-row justify="center" v-if="isLoggedIn">
        <v-col cols="8" id="latest-containers">
          <latest-containers></latest-containers>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';

import LatestContainers from '@/components/LatestContainers.vue';

export default Vue.extend({
  name: 'Home',
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    backendUrl() {
      return process.env.VUE_APP_BACKEND_URL
    },
  },
  components: {
    LatestContainers,
  },
});
</script>

<template>
  <div class="home">
    <top-bar title="Hello, Hinkskalle speaking!"></top-bar>
    <v-container>
        <v-row>
          <v-col cols="12">
            <h2>How To Use Me</h2>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-card tile height="100%">
              <v-card-title>
                Pull Only:
              </v-card-title>
              <v-card-subtitle>(no account necessary)</v-card-subtitle>
              <v-card-text>
                <pre>
singularity remote add --nologin \
  hinkskalle {{backendUrl}}
singularity remote use hinkskalle
                </pre>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="6">
            <v-card tile height="100%">
              <v-card-title>
                Pull and Push:
              </v-card-title>
              <v-card-subtitle>
                (<span v-show="!isLoggedIn">log in and </span>get a token)
              </v-card-subtitle>
              <v-card-text>
                <pre>
singularity remote add \
  hinkskalle {{backendUrl}}
# paste token
singularity remote use hinkskalle
# or (can also be done later)
singularity remote login hinkskalle
                </pre>
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
        <v-col cols="12" md="6" id="latest-containers">
          <latest-containers></latest-containers>
        </v-col>
        <v-col cols="12" md="6" id="latest-containers">
          <starred-containers></starred-containers>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import { getEnv } from '@/util/env';

import LatestContainers from '@/components/LatestContainers.vue';
import StarredContainers from '@/components/StarredContainers.vue';

export default Vue.extend({
  name: 'Home',
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    backendUrl(): string {
      return getEnv('VUE_APP_BACKEND_URL') as string
    },
  },
  components: {
    LatestContainers,
    StarredContainers,
  },
});
</script>

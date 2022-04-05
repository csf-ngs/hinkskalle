<template>

  <div class="home">
    <top-bar title="Hello, Hinkskalle speaking!"></top-bar>
    <v-container>
        <v-row>
          <v-col cols="12">
            <h2>This is How You Use Me</h2>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-tabs v-model="localState.usageTab" light centered>
              <v-tab>Singularity</v-tab>
              <v-tab>Docker</v-tab>
              <v-tab>ORAS</v-tab>
              <v-tab>CLI</v-tab>
            </v-tabs>
          </v-col>
        </v-row>
        <v-tabs-items class="pb-4" v-model="localState.usageTab">
          <v-tab-item>
            <v-row>
              <v-col cols="12" md="8" offset-md="2">
                <v-card tile height="100%">
                  <v-card-title>
                    Singularity Pull and Push:
                  </v-card-title>
                  <v-card-subtitle>
                    Compatible with the <a href="https://sylabs.io/">Singularity</a> library protocol.  
                    <span v-if="!isLoggedIn">
                      Unauthenticated users can only pull!
                    </span>
                    <span v-else>
                      <router-link to="/tokens">Get your token here.</router-link>
                    </span>
                  </v-card-subtitle>
                  <v-card-text>
                    <pre v-if="isLoggedIn">
  singularity remote add hinkskalle {{backendUrl}}
  # paste token
  singularity remote use hinkskalle
  # or (can also be done later)
  singularity remote login hinkskalle
  singularity push yourimage.sif library://{{currentUser.username}}/[collection]/[container]:[tag]
  singularity pull library://{{currentUser.username}}/[collection]/[container]:[tag]
                    </pre>
                    <pre v-else>
  singularity remote add --no-login hinkskalle {{backendUrl}}
  singularity remote use hinkskalle
  singularity pull library://pipeline/samtools:v1.9 # or other public containers
                    </pre>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-tab-item>
          <v-tab-item>
            <v-row>
              <v-col cols="12" md="8" offset-md="2">
                <v-card tile height="100%">
                  <v-card-title>
                    Docker Pull and Push
                  </v-card-title>
                  <v-card-subtitle>
                    Hinkskalle can be your <a href="https://www.docker.com/">docker</a> (OCI) registry! (<a href="https://podman.io/">podman</a> is also spoken here)
                  </v-card-subtitle>
                  <v-card-text>
                    <pre v-if="isLoggedIn">
  docker login -u {{currentUser.username}} {{referenceBase}}
  docker push {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag]
  docker pull {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag]
                    </pre>
                    <p v-else>
                      Only available for registered users.
                    </p>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-tab-item>
          <v-tab-item>
            <v-row>
              <v-col cols="12" md="8" offset-md="2">
                <v-card tile height="100%">
                  <v-card-title>
                    ORAS Pull and Push
                  </v-card-title>
                  <v-card-subtitle>
                    Use <a href="https://oras.land/#cli-installation">ORAS</a> to store/retrieve any files/directories
                  </v-card-subtitle>
                  <v-card-text>
                    <pre v-if="isLoggedIn">
  oras login <span v-if="!hasHttps">--insecure</span> -u {{currentUser.username}} {{referenceBase}}
  oras push <span v-if="!hasHttps">--plain-http</span> {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag] \
    file1 file2 ...
  oras pull <span v-if="!hasHttps">--plain-http</span> {{referenceBase}}/{{currentUser.username}}/[collection]/[container]:[tag] 
                    </pre>
                    <p v-else>
                      Only available for registered users.
                    </p>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-tab-item>
          <v-tab-item>
            <v-row>
              <v-col cols="12" md="8" offset-md="2">
                <v-card tile height="100%">
                  <v-card-title>
                    Hinksalle-CLI Pull and Push
                  </v-card-title>
                  <v-card-subtitle>
                    Our <a href="http://github.com/csf-ngs/hinkskalle-api">Python CLI</a> makes it easy to store and retrieve any files
                  </v-card-subtitle>
                  <v-card-text>
                    <pre v-if="isLoggedIn">
    pip3 install git+http://github.com/csf-ngs/hinkskalle-api
    hinkli --base {{backendUrl}} login
    hinkli push file1 {{currentUser.username}}/[collection]/[container]:[tag]
    hinkli pull {{currentUser.username}}/[collection]/[container]:[tag]
                    </pre>
                    <p v-else>
                      Only available for registered users.
                    </p>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-tab-item>
        </v-tabs-items>
      <v-row justify="center" v-if="!isLoggedIn">
        <v-col cols="6" id="login-msg" justify="center">
          <v-card elevation="1" color="yellow lighten-3" :to="'/login'">
            <v-card-title><v-icon>mdi-account-alert</v-icon> Not sure who you are! Please log in.</v-card-title>
          </v-card>
        </v-col>
      </v-row>
      <v-row justify="center" v-if="isLoggedIn">
        <v-col cols="12" md="6" id="latest-containers">
          <latest-containers></latest-containers>
        </v-col>
        <v-col cols="12" md="6" id="starred-containers">
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
import { User } from '@/store/models';

interface State {
  usageTab: any;
}

export default Vue.extend({
  name: 'HskHome',
  data: (): { localState: State } => ({
    localState: {
      usageTab: 0,
    },
  }),
  computed: {
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    backendUrl(): string {
      return getEnv('VUE_APP_BACKEND_URL') as string
    },
    hasHttps(): boolean {
      return this.backendUrl.startsWith('https');
    },
    referenceBase(): string {
      return this.backendUrl.replace(/^https?:\/\//, '').replace(/\/$/, '');
    },
  },
  components: {
    LatestContainers,
    StarredContainers,
  },
});
</script>

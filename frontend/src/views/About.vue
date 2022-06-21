<template>
  <div class="about">
    <top-bar title="Some Help!"></top-bar>
    <v-container>
          <v-card>
          <v-tabs vertical>
            <v-tab>
              About
            </v-tab>
            <v-tab>
              API
            </v-tab>
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  <h3>This is Hinkskalle {{frontendVersion}}!</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>Hinkskalle started out as a Singularity container registry compatible with the library 
                    protocol (similar to <a href="https://cloud.sylabs.io/">the Sylabs Cloud</a>), but expanded
                    into a general purpose registry supporting the 
                    <a href="https://github.com/opencontainers/distribution-spec">OCI distribution</a> 
                    protocol (docker, podman, ORAS) and arbitrary data.</p>
                  <p>Read all about it: <a href="https://csf-ngs.github.io/hinkskalle/user-docs/">User Documentation</a></p>
                </v-card-text>
              </v-card>
            </v-tab-item>
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  <h3>JSON API</h3>
                </v-card-subtitle>
                <v-card-text>
                  You can find the auto-generated Swagger/OpenAPI 2.0 specs <a href="/swagger/ui">here</a>
                </v-card-text>
                <v-card-subtitle>
                  <h3>Python Module/CLI</h3>
                </v-card-subtitle>
                <v-card-text>
                  Please check out the companion <a href="https://github.com/csf-ngs/hinkskalle-api">hinkskalle-api</a>
                </v-card-text>
              </v-card>
            </v-tab-item>
          </v-tabs>
          </v-card>
    </v-container>
  </div>
</template>
<style scoped>
.v-card__subtitle, .v-card__text {
  font-size: 1rem;
}

</style>
<script lang="ts">
import { version } from '../../package.json';
import { User } from '@/store/models';
import { getEnv } from '@/util/env';
import Vue from 'vue';

export default Vue.extend({
  name: 'HskAbout',
  data: () => ({
    frontendVersion: version,
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
});
</script>
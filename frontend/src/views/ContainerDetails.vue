<template>
  <div class="container-details">
    <top-bar title="Container Details">
    </top-bar>
    <error-message v-if="localState.error" :error="localState.error"></error-message>
    <v-container v-if="localState.container">
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-row>
            <v-col>
              <h1 class="justify-center d-flex">
                <router-link class="text-decoration-none" :to="{ name: 'Collections', params: { entity: localState.container.entityName } }">{{localState.container.entityName}}</router-link>/<router-link class="text-decoration-none" :to="{ name: 'Containers', params: { entity: localState.container.entityName, collection: localState.container.collectionName } }">{{localState.container.collectionName}}</router-link>/{{localState.container.name}}
                <container-stars :container="localState.container"></container-stars>
                <v-badge :content="localState.container.downloadCount || '0'" inline color="blue-grey lighten-1" class="px-1">
                  <v-icon>mdi-download</v-icon>
                </v-badge>
                <a v-if="localState.container.vcsUrl" :href="localState.container.vcsUrl" class="text-decoration-none d-flex align-center">
                  <v-icon>mdi-source-repository</v-icon>
                </a>
              </h1>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <hsk-text-input label="Name" :static-value="localState.container.name"></hsk-text-input>
            </v-col>
          </v-row>
          <v-row dense>
            <v-col>
              <hsk-text-input label="Created" :static-value="localState.container.createdAt | prettyDateTime"></hsk-text-input>
            </v-col>
            <v-col>
              <hsk-text-input label="Created By" :static-value="localState.container.createdBy"></hsk-text-input>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-expansion-panels>
            <v-expansion-panel>
              <v-expansion-panel-header>
                Details
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <v-row>
                  <v-col>
                    <hsk-text-input 
                      label="Git/VCS URL" 
                      field="vcsUrl" 
                      :obj="localState.container" 
                      action="containers/update"
                      :readonly="!canEdit"
                      @updated="localState.container=$event"></hsk-text-input>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <hsk-text-input 
                      label="Description" 
                      field="description" 
                      :obj="localState.container" 
                      action="containers/update"
                      :readonly="!canEdit"
                      @updated="localState.container=$event"></hsk-text-input>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <hsk-text-input 
                      type="textarea"
                      label="Full Description" 
                      field="fullDescription" 
                      :obj="localState.container" 
                      action="containers/update"
                      :readonly="!canEdit"
                      @updated="localState.container=$event"></hsk-text-input>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <hsk-text-input
                      type="yesno"
                      label="Private"
                      field="private"
                      :obj="localState.container"
                      action="containers/update"
                      :readonly="!canEdit"
                      @updated="localState.container=$event"></hsk-text-input>
                  </v-col>
                  <v-col>
                    <hsk-text-input
                      type="yesno"
                      label="Readonly"
                      field="readOnly"
                      :obj="localState.container"
                      action="containers/update"
                      :readonly="!localState.container.canEdit"
                      @updated="localState.container=$event"></hsk-text-input>
                  </v-col>
                </v-row>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <template v-if="localState.container.type==='singularity'">
            <h3 class="mb-2 d-flex">
              Images
              <v-spacer></v-spacer>
              <v-btn text color="primary darken-1" @click="loadImages()"><v-icon>mdi-refresh</v-icon></v-btn>
            </h3>
            <v-expansion-panels inset>
              <image-details 
                v-for="image in images"
                :key="image.id"
                :readonly="localState.container.readOnly"
                :image="image"></image-details>
            </v-expansion-panels>
          </template>
          <template v-else>
            <h4 class="mb-2 d-flex">
              Tags
              <v-spacer></v-spacer>
              <v-btn text color="primary darken-1" @click="loadManifests()"><v-icon>mdi-refresh</v-icon></v-btn>
            </h4>
            <v-expansion-panels inset>
              <manifest-details
                v-for="manifest in manifests"
                :key="manifest.id"
                :manifest="manifest"></manifest-details>
            </v-expansion-panels>
          </template>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import ImageDetails from '@/components/ImageDetails.vue';
import ManifestDetails from '@/components/ManifestDetails.vue';

import Vue from 'vue';
import { Container, Image, Manifest, User } from '../store/models';

import { orderBy as _orderBy } from 'lodash';

interface State {
  container: Container | null;
  error: string | null;
}

export default Vue.extend({
  components: { ImageDetails, ManifestDetails, },
  name: 'ContainerDetails',
  mounted() {
    this.loadContainer();
  },
  data: (): { localState: State } => ({
    localState: {
      container: null,
      error: null,
    }
  }),
  watch: {
    $route() {
      this.loadContainer();
    }
  },
  computed: {
    title(): string {
      return `${this.localState.container ? this.localState.container.fullPath : '...'}`
    },
    loading(): boolean {
      return this.$store.getters['container/status']==='loading';
    },
    images(): Image[] {
      return _orderBy(this.$store.getters['images/list'], 'createdAt', 'desc');
    },
    manifests(): Manifest[] {
      return _orderBy(this.$store.getters['manifests/list'], 'createdAt', 'desc');
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
    canEdit(): boolean {
      return this.localState.container !== null && !this.localState.container.readOnly && this.localState.container.canEdit
    }
  },
  methods: {
    loadContainer() {
      this.localState.error = null;
      this.$store.dispatch('containers/get', { entityName: this.$route.params.entity, collectionName: this.$route.params.collection, containerName: this.$route.params.container })
        .then((container: Container) => {
          this.localState.container = container;
          if (container.type === 'singularity') {
            this.loadImages();
          }
          else {
            this.loadManifests();
          }
        })
        .catch(err => {
          this.localState.error = err;
        });
    },
    loadManifests() {
      this.$store.dispatch('manifests/list', this.localState.container)
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
    loadImages() {
      this.$store.dispatch('images/list', this.localState.container)
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    }
  },
});
</script>